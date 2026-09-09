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


def test_exit_before_min_holding_is_ignored():
    """min_holding_steps 이전의 EXIT은 무시되고, 대신 그 스텝의 미실현손익 변화가
    보상으로 반영된다(신호가 약한 구간에서 조기 청산해 노이즈에 학습되는 것을 방지)."""
    env = PairSpreadEnv(_make_features(), fee_rate=0.001, min_holding_steps=2, max_holding_steps=5)
    env.reset()
    env.step(Action.ENTER_LONG)
    entry_spread = env._entry_spread
    obs, reward, terminated, truncated, info = env.step(Action.EXIT)
    current_spread = env.df.iloc[env._step_idx - 1]["spread"]
    expected_delta = current_spread - entry_spread   # 아직 청산 안 됐으므로 수수료 없음
    assert reward == pytest.approx(expected_delta)
    assert obs[2] == 1.0  # 여전히 포지션 보유 중 — EXIT이 무시됨


def test_exit_after_min_holding_realizes_pnl_minus_fee():
    env = PairSpreadEnv(_make_features(), fee_rate=0.001, min_holding_steps=1, max_holding_steps=5)
    env.reset()
    env.step(Action.ENTER_LONG)
    entry_spread = env._entry_spread
    env.step(Action.HOLD)  # min_holding_steps(1)를 채운다
    obs, reward, terminated, truncated, info = env.step(Action.EXIT)
    current_spread = env.df.iloc[env._step_idx - 1]["spread"]
    prev_spread = env.df.iloc[env._step_idx - 2]["spread"]
    expected = (current_spread - prev_spread) - 0.001  # 마지막 스텝 delta - 청산 수수료
    assert reward == pytest.approx(expected)
    assert obs[2] == 0.0


def test_double_enter_keeps_existing_position():
    """이미 포지션이 있을 때 다시 ENTER_LONG을 보내도 포지션은 그대로 유지되고
    (재진입 아님), 그 스텝의 미실현손익 변화가 보상으로 반영된다."""
    env = PairSpreadEnv(_make_features(), fee_rate=0.001)
    env.reset()
    env.step(Action.ENTER_LONG)
    entry_spread = env._entry_spread
    obs, reward, terminated, truncated, info = env.step(Action.ENTER_LONG)
    current_spread = env.df.iloc[env._step_idx - 1]["spread"]
    assert reward == pytest.approx(current_spread - entry_spread)
    assert obs[2] == 1.0
    assert env._entry_spread == entry_spread  # 재진입으로 entry_spread가 갱신되지 않음
