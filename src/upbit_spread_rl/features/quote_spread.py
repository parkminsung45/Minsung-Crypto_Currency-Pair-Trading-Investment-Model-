"""오더북 호가 스프레드(마켓메이킹) 피처 계산."""
from __future__ import annotations

import pandas as pd


def compute_quote_features(orderbook_df: pd.DataFrame, depth: int = 5) -> pd.DataFrame:
    """오더북 스냅샷들로부터 마켓메이킹에 필요한 피처를 계산.

    Args:
        orderbook_df: 컬럼 [timestamp, bid_price_1..N, bid_size_1..N, ask_price_1..N, ask_size_1..N]
        depth: 사용할 호가 단수.
    """
    bid_prices = orderbook_df[[f"bid_price_{i}" for i in range(1, depth + 1)]]
    ask_prices = orderbook_df[[f"ask_price_{i}" for i in range(1, depth + 1)]]
    bid_sizes = orderbook_df[[f"bid_size_{i}" for i in range(1, depth + 1)]]
    ask_sizes = orderbook_df[[f"ask_size_{i}" for i in range(1, depth + 1)]]

    best_bid = bid_prices.iloc[:, 0]
    best_ask = ask_prices.iloc[:, 0]
    mid = (best_bid + best_ask) / 2
    spread = best_ask - best_bid
    spread_bps = spread / mid * 10_000

    bid_vol = bid_sizes.sum(axis=1)
    ask_vol = ask_sizes.sum(axis=1)
    imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol)

    return pd.DataFrame(
        {
            "timestamp": orderbook_df["timestamp"],
            "mid_price": mid,
            "spread": spread,
            "spread_bps": spread_bps,
            "order_imbalance": imbalance,
        }
    )
