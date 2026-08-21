import pandas as pd
import pytest

from upbit_spread_rl.features.quote_spread import compute_quote_features


def _make_orderbook_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=3, freq="s"),
            "bid_price_1": [100.0, 101.0, 102.0],
            "bid_size_1": [1.0, 1.0, 2.0],
            "ask_price_1": [100.2, 101.2, 102.4],
            "ask_size_1": [1.0, 2.0, 1.0],
        }
    )


def test_compute_quote_features_basic():
    df = compute_quote_features(_make_orderbook_df(), depth=1)
    assert list(df.columns) == [
        "timestamp",
        "mid_price",
        "spread",
        "spread_bps",
        "order_imbalance",
    ]
    assert df["mid_price"].iloc[0] == pytest.approx(100.1)
    assert df["spread"].iloc[0] == pytest.approx(0.2)


def test_order_imbalance_sign():
    df = compute_quote_features(_make_orderbook_df(), depth=1)
    # row0: bid_size=1, ask_size=1 -> balanced
    assert df["order_imbalance"].iloc[0] == pytest.approx(0.0)
    # row1: bid_size=1, ask_size=2 -> ask heavier -> negative imbalance
    assert df["order_imbalance"].iloc[1] < 0
