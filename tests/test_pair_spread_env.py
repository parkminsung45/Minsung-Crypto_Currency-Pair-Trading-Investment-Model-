import numpy as np
import pandas as pd
import pytest

from upbit_spread_rl.envs.pair_spread_env import Action, PairSpreadEnv


def _make_features(n: int = 20) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    price_a = 100 + np.cumsum(rng.normal(0, 1, n))
    price_b = 50 + np.cumsum(rng.normal(0, 0.5, n))
    spread = np.log(price_a) - np.log(price_b)
    return pd.DataFrame(
        {
            "price_a": price_a,
            "price_b": price_b,
            "spread": spread,
            "spread_zscore": (spread - spread.mean()) / spread.std(),
            "spread_change": np.diff(spread, prepend=spread[0]),
        }
    )


def test_reset_returns_flat_position_obs():
    env = PairSpreadEnv(_make_features())
    obs, info = env.reset()
    assert obs.shape == (5,)
    assert obs[2] == 0.0  # position flat


def test_enter_long_charges_fee_only():
    env = PairSpreadEnv(_make_features(), fee_rate=0.001)
    env.reset()
    obs, reward, terminated, truncated, info = env.step(Action.ENTER_LONG)
    assert reward == pytest.approx(-0.001)
    assert obs[2] == 1.0  # position long


def test_exit_realizes_pnl_minus_fee():
    env = PairSpreadEnv(_make_features(), fee_rate=0.001)
    env.reset()
    env.step(Action.ENTER_LONG)
    entry_spread = env._entry_spread
    obs, reward, terminated, truncated, info = env.step(Action.EXIT)
    current_spread = env.df.iloc[env._step_idx - 1]["spread"]
    expected = (current_spread - entry_spread) - 0.001
    assert reward == pytest.approx(expected)
    assert obs[2] == 0.0


def test_double_enter_is_noop_for_position():
    env = PairSpreadEnv(_make_features(), fee_rate=0.001)
    env.reset()
    env.step(Action.ENTER_LONG)
    obs, reward, terminated, truncated, info = env.step(Action.ENTER_LONG)
    assert reward == 0.0
    assert obs[2] == 1.0
