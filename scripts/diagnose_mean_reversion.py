"""페어 스프레드에 실제로 평균회귀 신호가 있는지 진단한다.

z-score와 향후 N스텝 뒤 스프레드 변화의 상관관계를 여러 horizon에 대해 측정한다.
평균회귀가 유효하면 이 상관관계가 뚜렷한 음수여야 한다(z가 높으면 이후 스프레드가
줄어들고, z가 낮으면 늘어나야 하므로). 0에 가까우면 이 기간엔 활용 가능한 신호가
없다는 뜻 — 모델을 재학습해도 노이즈에 오버피팅될 위험이 크다.

사용: python scripts/diagnose_mean_reversion.py --market-a KRW-BTC --market-b KRW-ETH --days 180
"""
from __future__ import annotations

import argparse
import datetime as dt

import pandas as pd

from upbit_spread_rl.data.storage import load_candles
from upbit_spread_rl.features.pair_spread import compute_spread


def _load_close_series(market: str, days: int) -> pd.Series:
    end = dt.date.today()
    frames = []
    for i in range(days):
        date = str(end - dt.timedelta(days=i))
        df = load_candles(market, date)
        if not df.empty:
            frames.append(df)
    if not frames:
        raise RuntimeError(f"{market}: 저장된 캔들 데이터가 없습니다.")
    full = pd.concat(frames).sort_values("timestamp").reset_index(drop=True)
    return full.set_index("timestamp")["close"]


def main(market_a: str, market_b: str, days: int, window: int) -> None:
    price_a = _load_close_series(market_a, days)
    price_b = _load_close_series(market_b, days)
    aligned = pd.concat([price_a, price_b], axis=1, keys=["price_a", "price_b"], sort=False).dropna()

    feat = compute_spread(aligned["price_a"], aligned["price_b"], window=window)
    df = pd.concat([aligned, feat], axis=1).dropna()
    print(f"{market_a}/{market_b}: {len(df)}행 ({df.index.min()} ~ {df.index.max()})")

    for horizon in [15, 30, 60, 120, 240, 480]:
        future_change = df["spread"].shift(-horizon) - df["spread"]
        corr = df["spread_zscore"].corr(future_change)
        n = df["spread_zscore"].notna().sum()
        verdict = "평균회귀 신호 있음" if corr < -0.05 else ("추세(모멘텀) 신호" if corr > 0.05 else "신호 거의 없음")
        print(f"  horizon={horizon:>4}분: corr(zscore, future_change) = {corr:+.4f}  [{verdict}]")

    # 참고용: z-score가 극단(|z|>2)일 때만 놓고 봐도 같은 경향인지
    extreme = df[df["spread_zscore"].abs() > 2]
    if len(extreme) > 30:
        future_change = df["spread"].shift(-60) - df["spread"]
        corr_extreme = extreme["spread_zscore"].corr(future_change.loc[extreme.index])
        print(f"  |z|>2 구간만(n={len(extreme)}), horizon=60분: corr = {corr_extreme:+.4f}")
    else:
        print(f"  |z|>2 구간이 {len(extreme)}행뿐 — 표본 부족으로 생략")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--market-a", default="KRW-BTC")
    parser.add_argument("--market-b", default="KRW-ETH")
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--window", type=int, default=240)
    args = parser.parse_args()

    main(args.market_a, args.market_b, args.days, args.window)
