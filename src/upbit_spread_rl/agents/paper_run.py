"""학습된 PPO 정책으로 페어 스프레드 페이퍼 트레이딩을 1회 실행한다.

실제 주문은 없다(PaperBroker). 업비트 REST로 최신 시세를 가져와 정책 액션을 결정하고,
포지션/평가액 상태를 페어별로 로컬에 유지하며 dashboard/data/history.json을 갱신한다.
여러 페어를 동시에 굴릴 수 있도록 상태 파일은 페어마다 분리되어 있고(paper_state_<A>_<B>.json),
한 번의 실행에서 모든 페어를 순회한 뒤 포트폴리오 가치/비중을 합산해 history.json에
레코드 1건으로 남긴다.
GitHub Actions 워크플로우(.github/workflows/paper_trading.yml)가 이 함수를 1시간마다 호출한다.
"""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
from stable_baselines3 import PPO

from upbit_spread_rl.envs.pair_spread_env import Action, Position
from upbit_spread_rl.features.pair_spread import compute_spread
from upbit_spread_rl.utils.config import PROJECT_ROOT
from upbit_spread_rl.utils.dashboard_export import append_record
from upbit_spread_rl.utils.rate_limiter import TokenBucketLimiter

UPBIT_REST_BASE = "https://api.upbit.com/v1"
STATE_DIR = PROJECT_ROOT / "dashboard" / "data"
DEFAULT_INITIAL_CASH_KRW = 1_000_000.0
FEE_RATE = 0.0005
WINDOW = 240  # 스프레드 z-score 롤링 윈도우(분봉 개수)
LOOKBACK_MINUTES = WINDOW * 3  # 워밍업 여유분 포함

# 동시에 굴리는 페어 목록. 페어를 추가하려면 (market_a, market_b) 튜플만 더하고
# models/pair_spread_<A>_<B>.zip 을 학습해 두면 된다.
DEFAULT_PAIRS: list[tuple[str, str]] = [
    ("KRW-BTC", "KRW-ETH"),
    ("KRW-XRP", "KRW-SOL"),
]

# 여러 페어가 순차적으로 같은 클라이언트를 공유해 호출하므로, 전역 리미터 하나로
# 업비트 시세 조회 그룹의 초당 한도(429 Too Many Requests 방지)를 지킨다.
_rate_limiter = TokenBucketLimiter(rate_per_sec=3.0, burst=3)


@dataclass
class PairResult:
    market_a: str
    market_b: str
    symbol_a: str
    symbol_b: str
    portfolio_value: float
    long_weight: float   # 페어 내 총자산 대비 롱 다리 비중(부호 있음)
    short_weight: float  # 페어 내 총자산 대비 숏 다리 비중(부호 있음)
    action_a: str
    action_b: str


def _state_path(market_a: str, market_b: str) -> Path:
    tag = f"{market_a.split('-')[1]}_{market_b.split('-')[1]}"
    return STATE_DIR / f"paper_state_{tag}.json"


def _load_state(market_a: str, market_b: str) -> dict:
    path = _state_path(market_a, market_b)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {
        "cash_krw": DEFAULT_INITIAL_CASH_KRW,
        "position": Position.FLAT.value,
        "entry_spread": 0.0,
        "entry_price_a": 0.0,
        "entry_price_b": 0.0,
        "coin_a_qty": 0.0,
        "coin_b_qty": 0.0,
    }


def _save_state(market_a: str, market_b: str, state: dict) -> None:
    path = _state_path(market_a, market_b)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


async def _fetch_recent_minutes(market: str, count: int, client: httpx.AsyncClient) -> pd.DataFrame:
    rows: list[dict] = []
    to_param = None
    remaining = count
    while remaining > 0:
        batch_count = min(200, remaining)
        params = {"market": market, "count": batch_count}
        if to_param:
            params["to"] = to_param
        await _rate_limiter.acquire()
        resp = await client.get(f"{UPBIT_REST_BASE}/candles/minutes/1", params=params)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        rows.extend(batch)
        oldest = min(batch, key=lambda c: c["candle_date_time_utc"])
        to_param = oldest["candle_date_time_utc"]
        remaining -= len(batch)

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["candle_date_time_utc"], utc=True)
    df = df.rename(columns={"trade_price": "close"})
    df = df[["timestamp", "close"]].sort_values("timestamp").drop_duplicates("timestamp")
    return df.reset_index(drop=True)


async def _run_pair(
    market_a: str,
    market_b: str,
    model_path: str | Path | None,
    client: httpx.AsyncClient,
) -> PairResult:
    """페어 하나의 페이퍼 트레이딩을 1스텝 진행하고 결과를 반환한다(기록은 호출부에서 합산 후 남김)."""
    if model_path is None:
        model_path = PROJECT_ROOT / "models" / f"pair_spread_{market_a}_{market_b}.zip"
    model = PPO.load(str(model_path))
    state = _load_state(market_a, market_b)

    candles_a = await _fetch_recent_minutes(market_a, LOOKBACK_MINUTES, client)
    candles_b = await _fetch_recent_minutes(market_b, LOOKBACK_MINUTES, client)

    aligned = pd.concat(
        [candles_a.set_index("timestamp")["close"], candles_b.set_index("timestamp")["close"]],
        axis=1,
        keys=["price_a", "price_b"],
    ).dropna()

    spread_features = compute_spread(aligned["price_a"], aligned["price_b"], window=WINDOW)
    df = pd.concat([aligned, spread_features], axis=1).dropna()
    if df.empty:
        raise RuntimeError(f"{market_a}/{market_b}: 스프레드 피처 계산 결과가 비어있습니다 (데이터 부족)")

    latest = df.iloc[-1]
    obs = [
        float(latest["spread_zscore"]),
        float(latest["spread_change"]),
        float(state["position"]),
        0.0,  # unrealized_pnl 근사값(관측만 사용, 학습 시와 스케일 차이는 허용)
        0.0,
    ]
    price_a, price_b = float(latest["price_a"]), float(latest["price_b"])
    current_spread = float(latest["spread"])
    if state["position"] != Position.FLAT.value:
        direction = 1 if state["position"] == Position.LONG.value else -1
        obs[3] = direction * (current_spread - state["entry_spread"])

    action_id, _ = model.predict(np.array(obs, dtype=np.float32), deterministic=True)
    action = Action(int(action_id))

    position = Position(state["position"])
    action_taken = "HOLD"

    notional_per_leg = state["cash_krw"] * 0.3  # 스프레드 한 다리당 명목 투입 비율(보수적)

    if action == Action.ENTER_LONG and position == Position.FLAT:
        qty_a = notional_per_leg / price_a
        qty_b = notional_per_leg / price_b
        fee = notional_per_leg * FEE_RATE * 2
        state["cash_krw"] -= fee
        state["coin_a_qty"] = qty_a
        state["coin_b_qty"] = -qty_b
        state["position"] = Position.LONG.value
        state["entry_spread"] = current_spread
        state["entry_price_a"] = price_a
        state["entry_price_b"] = price_b
        action_taken = "BUY"
    elif action == Action.ENTER_SHORT and position == Position.FLAT:
        qty_a = notional_per_leg / price_a
        qty_b = notional_per_leg / price_b
        fee = notional_per_leg * FEE_RATE * 2
        state["cash_krw"] -= fee
        state["coin_a_qty"] = -qty_a
        state["coin_b_qty"] = qty_b
        state["position"] = Position.SHORT.value
        state["entry_spread"] = current_spread
        state["entry_price_a"] = price_a
        state["entry_price_b"] = price_b
        action_taken = "SELL"
    elif action == Action.EXIT and position != Position.FLAT:
        pnl_a = state["coin_a_qty"] * (price_a - state["entry_price_a"])
        pnl_b = state["coin_b_qty"] * (price_b - state["entry_price_b"])
        fee = abs(state["coin_a_qty"]) * price_a * FEE_RATE + abs(state["coin_b_qty"]) * price_b * FEE_RATE
        state["cash_krw"] += pnl_a + pnl_b - fee
        state["coin_a_qty"] = 0.0
        state["coin_b_qty"] = 0.0
        state["position"] = Position.FLAT.value
        state["entry_spread"] = 0.0
        action_taken = "SELL" if position == Position.LONG else "BUY"

    mark_to_market = state["cash_krw"]
    if state["position"] != Position.FLAT.value:
        mark_to_market += state["coin_a_qty"] * price_a + state["coin_b_qty"] * price_b

    notional_a = state["coin_a_qty"] * price_a
    notional_b = state["coin_b_qty"] * price_b

    _save_state(market_a, market_b, state)

    return PairResult(
        market_a=market_a,
        market_b=market_b,
        symbol_a=market_a.split("-")[1],
        symbol_b=market_b.split("-")[1],
        portfolio_value=mark_to_market,
        long_weight=notional_a / mark_to_market if mark_to_market > 0 else 0.0,
        short_weight=notional_b / mark_to_market if mark_to_market > 0 else 0.0,
        action_a=action_taken,
        action_b=action_taken,
    )


async def run_all(pairs: list[tuple[str, str]] | None = None, dry_run: bool = True) -> dict:
    """등록된 모든 페어를 1스텝씩 실행하고, 합산된 포트폴리오 상태를 history.json에 1건 남긴다.

    아직 모델이 학습되지 않은 페어(models/pair_spread_<A>_<B>.zip 없음)는 건너뛴다 —
    새 페어를 DEFAULT_PAIRS에 먼저 등록해두고 나중에 모델을 채워 넣는 배치가 가능하도록.
    """
    pairs = pairs or DEFAULT_PAIRS
    runnable = [
        (a, b) for a, b in pairs
        if (PROJECT_ROOT / "models" / f"pair_spread_{a}_{b}.zip").exists()
    ]
    if not runnable:
        raise RuntimeError("실행 가능한 페어가 없습니다 (학습된 모델을 찾지 못함)")

    async with httpx.AsyncClient(timeout=15.0) as client:
        results = [await _run_pair(a, b, None, client) for a, b in runnable]

    total_value = sum(r.portfolio_value for r in results)
    weights: dict[str, float] = {}
    actions: dict[str, str] = {}
    total_exposure = 0.0

    for r in results:
        share = r.portfolio_value / total_value if total_value > 0 else 0.0
        weights[r.symbol_a] = weights.get(r.symbol_a, 0.0) + r.long_weight * share
        weights[r.symbol_b] = weights.get(r.symbol_b, 0.0) + r.short_weight * share
        actions[r.symbol_a] = r.action_a
        actions[r.symbol_b] = r.action_b
        total_exposure += (abs(r.long_weight) + abs(r.short_weight)) * share

    weights["CASH"] = max(1.0 - total_exposure, 0.0)

    now = dt.datetime.now(dt.timezone.utc)
    date_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    append_record(
        date=date_str,
        portfolio_value=total_value,
        weights=weights,
        actions=actions,
        dry_run=dry_run,
    )

    return {
        "date": date_str,
        "portfolio_value": total_value,
        "pairs": [
            {"market_a": r.market_a, "market_b": r.market_b, "portfolio_value": r.portfolio_value}
            for r in results
        ],
    }


async def run_once(
    market_a: str = "KRW-BTC",
    market_b: str = "KRW-ETH",
    model_path: str | Path | None = None,
    dry_run: bool = True,
) -> dict:
    """단일 페어만 실행하고 기록한다(하위 호환용 — 신규 코드는 run_all 사용을 권장)."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        result = await _run_pair(market_a, market_b, model_path, client)

    weights = {
        result.symbol_a: result.long_weight,
        result.symbol_b: result.short_weight,
        "CASH": max(1.0 - abs(result.long_weight) - abs(result.short_weight), 0.0),
    }
    now = dt.datetime.now(dt.timezone.utc)
    date_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    append_record(
        date=date_str,
        portfolio_value=result.portfolio_value,
        weights=weights,
        actions={result.symbol_a: result.action_a, result.symbol_b: result.action_b},
        dry_run=dry_run,
    )

    return {
        "date": date_str,
        "portfolio_value": result.portfolio_value,
    }
