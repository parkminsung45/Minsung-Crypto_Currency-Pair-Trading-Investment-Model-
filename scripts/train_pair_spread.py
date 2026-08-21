"""저장된 캔들 데이터로 페어 스프레드 PPO 정책을 학습한다.

사용: python scripts/train_pair_spread.py --market-a KRW-BTC --market-b KRW-ETH --days 30
"""
from __future__ import annotations

import argparse
import datetime as dt

import pandas as pd

from upbit_spread_rl.agents.train import train_ppo
from upbit_spread_rl.data.storage import load_candles
from upbit_spread_rl.envs.pair_spread_env import PairSpreadEnv
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
        raise RuntimeError(f"{market}: 저장된 캔들 데이터가 없습니다. collect_candles.py를 먼저 실행하세요.")
    full = pd.concat(frames).sort_values("timestamp").reset_index(drop=True)
    return full.set_index("timestamp")["close"]


def build_features(market_a: str, market_b: str, days: int, window: int = 240) -> pd.DataFrame:
    price_a = _load_close_series(market_a, days)
    price_b = _load_close_series(market_b, days)
    aligned = pd.concat([price_a, price_b], axis=1, keys=["price_a", "price_b"]).dropna()

    spread_features = compute_spread(aligned["price_a"], aligned["price_b"], window=window)
    df = pd.concat([aligned, spread_features], axis=1).dropna()
    return df.reset_index(drop=True)


def main(market_a: str, market_b: str, days: int, timesteps: int) -> None:
    df = build_features(market_a, market_b, days)
    print(f"학습 데이터: {len(df)} 스텝 ({market_a} vs {market_b})")

    def env_factory():
        return PairSpreadEnv(df)

    train_ppo(
        env_factory,
        total_timesteps=timesteps,
        model_out_path=f"models/pair_spread_{market_a}_{market_b}.zip",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--market-a", default="KRW-BTC")
    parser.add_argument("--market-b", default="KRW-ETH")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--timesteps", type=int, default=200_000)
    args = parser.parse_args()

    main(args.market_a, args.market_b, args.days, args.timesteps)
