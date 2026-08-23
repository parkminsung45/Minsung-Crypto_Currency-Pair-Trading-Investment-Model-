"""1시간 단위 페이퍼 트레이딩 실행 사이클.

학습된 PPO 정책이 아직 없으므로, 베이스라인으로 z-score 임계값 규칙 정책을 사용한다.
정책은 상태 파일(logs/paper_state.json)에 포지션/잔고를 유지해 실행 간 이어간다.
"""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import httpx
import pandas as pd

from upbit_spread_rl.data.candle_fetcher import CandleFetcher
from upbit_spread_rl.data.storage import save_candles
from upbit_spread_rl.execution.broker import Order
from upbit_spread_rl.execution.paper_broker import PaperBroker
from upbit_spread_rl.execution.risk_guard import RiskGuard
from upbit_spread_rl.features.pair_spread import compute_spread
from upbit_spread_rl.utils.config import PROJECT_ROOT, MarketConfig, load_market_config
from upbit_spread_rl.utils.dashboard_export import append_record

STATE_PATH = PROJECT_ROOT / "logs" / "paper_state.json"

ENTRY_Z = 2.0
EXIT_Z = 0.5
LOOKBACK_DAYS = 5
HEDGE_WINDOW = 240


@dataclass
class PaperState:
    balances: dict[str, float]
    position: str = "FLAT"  # FLAT | LONG | SHORT
    entry_spread: float = 0.0

    @classmethod
    def load(cls) -> "PaperState":
        if STATE_PATH.exists():
            with open(STATE_PATH, encoding="utf-8") as f:
                return cls(**json.load(f))
        return cls(balances={"KRW": 1_000_000.0})

    def save(self) -> None:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)


async def _refresh_recent_candles(market: str, fetcher: CandleFetcher, client: httpx.AsyncClient) -> pd.DataFrame:
    """최근 LOOKBACK_DAYS치를 다시 받아 raw 파티션을 갱신하고, 합쳐진 종가 시계열을 반환."""
    end = dt.datetime.now(dt.timezone.utc)
    start = end - dt.timedelta(days=LOOKBACK_DAYS)
    df = await fetcher.fetch_range(market, start, end, client)
    if df.empty:
        raise RuntimeError(f"{market}: 캔들 수집 실패(빈 응답)")

    for date, group in df.groupby(df["timestamp"].dt.date):
        save_candles(group, market, str(date))

    return df


def _decide_action(zscore: float, position: str) -> str:
    if position == "FLAT":
        if zscore >= ENTRY_Z:
            return "ENTER_SHORT"
        if zscore <= -ENTRY_Z:
            return "ENTER_LONG"
        return "HOLD"
    if abs(zscore) <= EXIT_Z:
        return "EXIT"
    return "HOLD"


async def run_once(config: MarketConfig | None = None) -> dict:
    """한 사이클 실행: 데이터 갱신 → 스프레드 계산 → 규칙 정책 결정 → 페이퍼 체결 → 기록.

    Returns: dashboard history에 기록된 레코드(dict).
    """
    config = config or load_market_config()
    market_a, market_b = config.pair_markets[0], config.pair_markets[1]

    fetcher = CandleFetcher(unit_minutes=config.candle_unit_minutes)
    async with httpx.AsyncClient(timeout=10.0) as client:
        df_a = await _refresh_recent_candles(market_a, fetcher, client)
        df_b = await _refresh_recent_candles(market_b, fetcher, client)

    merged = pd.merge(
        df_a[["timestamp", "close"]].rename(columns={"close": "price_a"}),
        df_b[["timestamp", "close"]].rename(columns={"close": "price_b"}),
        on="timestamp",
        how="inner",
    ).sort_values("timestamp")

    if len(merged) < HEDGE_WINDOW + 1:
        raise RuntimeError(
            f"헤지비율 추정에 필요한 최소 데이터 부족: {len(merged)}행 < {HEDGE_WINDOW + 1}행"
        )

    spread_df = compute_spread(merged["price_a"], merged["price_b"], window=HEDGE_WINDOW)
    latest = spread_df.iloc[-1]
    latest_price_a = merged["price_a"].iloc[-1]
    latest_price_b = merged["price_b"].iloc[-1]

    if pd.isna(latest["spread_zscore"]):
        raise RuntimeError("스프레드 z-score가 NaN — 워밍업 구간 데이터 부족")

    state = PaperState.load()
    broker = PaperBroker(fee_rate=config.fee_rate, balances=dict(state.balances))
    risk_guard = RiskGuard(daily_loss_limit_krw=100_000.0, max_position_krw=500_000.0)

    action = _decide_action(float(latest["spread_zscore"]), state.position)
    actions_log = {market_a: "HOLD", market_b: "HOLD"}

    order_notional_krw = 200_000.0

    if action == "ENTER_LONG":
        risk_guard.check_order_allowed(order_notional_krw)
        await _fill_pair(broker, market_a, market_b, latest_price_a, latest_price_b, order_notional_krw, buy_a=True)
        state.position = "LONG"
        state.entry_spread = float(latest["spread"])
        actions_log = {market_a: "BUY", market_b: "SELL"}
    elif action == "ENTER_SHORT":
        risk_guard.check_order_allowed(order_notional_krw)
        await _fill_pair(broker, market_a, market_b, latest_price_a, latest_price_b, order_notional_krw, buy_a=False)
        state.position = "SHORT"
        state.entry_spread = float(latest["spread"])
        actions_log = {market_a: "SELL", market_b: "BUY"}
    elif action == "EXIT" and state.position != "FLAT":
        buy_a = state.position == "SHORT"
        await _fill_pair(broker, market_a, market_b, latest_price_a, latest_price_b, order_notional_krw, buy_a=buy_a)
        actions_log = (
            {market_a: "BUY", market_b: "SELL"} if buy_a else {market_a: "SELL", market_b: "BUY"}
        )
        state.position = "FLAT"
        state.entry_spread = 0.0

    state.balances = broker.balances
    state.save()

    coin_a = market_a.split("-")[1]
    coin_b = market_b.split("-")[1]
    portfolio_value = (
        broker.balances.get("KRW", 0.0)
        + broker.balances.get(coin_a, 0.0) * latest_price_a
        + broker.balances.get(coin_b, 0.0) * latest_price_b
    )
    total = portfolio_value if portfolio_value > 0 else 1.0
    weights = {
        coin_a: (broker.balances.get(coin_a, 0.0) * latest_price_a) / total,
        coin_b: (broker.balances.get(coin_b, 0.0) * latest_price_b) / total,
        "CASH": broker.balances.get("KRW", 0.0) / total,
    }

    timestamp_key = merged["timestamp"].iloc[-1].strftime("%Y-%m-%dT%H:%M")
    record = append_record(
        date=timestamp_key,
        portfolio_value=portfolio_value,
        weights=weights,
        actions=actions_log,
        dry_run=True,
    )
    return record[-1]


async def _fill_pair(
    broker: PaperBroker,
    market_a: str,
    market_b: str,
    price_a: float,
    price_b: float,
    notional_krw: float,
    buy_a: bool,
) -> None:
    """페어의 한쪽은 매수, 한쪽은 매도로 즉시 체결(시장가 근사) — notional_krw를 동일 배분."""
    half = notional_krw / 2
    side_a: str = "bid" if buy_a else "ask"
    side_b: str = "ask" if buy_a else "bid"

    order_a = await broker.place_order(
        Order(market=market_a, side=side_a, price=price_a, volume=half / price_a)
    )
    broker.fill_order(order_a.order_id)

    order_b = await broker.place_order(
        Order(market=market_b, side=side_b, price=price_b, volume=half / price_b)
    )
    broker.fill_order(order_b.order_id)
