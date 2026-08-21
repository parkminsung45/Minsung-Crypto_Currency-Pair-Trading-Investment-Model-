"""페어 스프레드(통계적 차익거래) Gymnasium 환경.

행동: 0=유지/청산상태 유지, 1=롱 스프레드 진입, 2=숏 스프레드 진입, 3=청산
상태: [spread_zscore, spread_change, position, unrealized_pnl, holding_steps]
보상: 스텝별 미실현손익 변화 - 진입/청산 시 수수료
"""
from __future__ import annotations

from enum import IntEnum

import gymnasium as gym
import numpy as np
import pandas as pd
from gymnasium import spaces


class Action(IntEnum):
    HOLD = 0
    ENTER_LONG = 1
    ENTER_SHORT = 2
    EXIT = 3


class Position(IntEnum):
    FLAT = 0
    LONG = 1
    SHORT = -1


class PairSpreadEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(
        self,
        features_df: pd.DataFrame,
        fee_rate: float = 0.0005,
        max_holding_steps: int = 500,
    ) -> None:
        """
        Args:
            features_df: pair_spread.compute_spread() 출력 + 원본 가격 컬럼(price_a, price_b),
                NaN(워밍업 구간)은 미리 제거되어 있어야 한다.
            fee_rate: 편도 수수료율(진입/청산 각각 적용).
            max_holding_steps: 포지션 강제 청산까지 최대 보유 스텝 수.
        """
        super().__init__()
        required_cols = {"spread", "spread_zscore", "spread_change", "price_a", "price_b"}
        missing = required_cols - set(features_df.columns)
        if missing:
            raise ValueError(f"features_df에 필요한 컬럼이 없습니다: {missing}")

        self.df = features_df.reset_index(drop=True)
        self.fee_rate = fee_rate
        self.max_holding_steps = max_holding_steps

        self.action_space = spaces.Discrete(len(Action))
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(5,), dtype=np.float32
        )

        self._step_idx = 0
        self._position = Position.FLAT
        self._entry_spread = 0.0
        self._holding_steps = 0

    def _get_obs(self) -> np.ndarray:
        row = self.df.iloc[self._step_idx]
        unrealized_pnl = self._unrealized_pnl(row["spread"])
        return np.array(
            [
                row["spread_zscore"],
                row["spread_change"],
                float(self._position.value),
                unrealized_pnl,
                float(self._holding_steps),
            ],
            dtype=np.float32,
        )

    def _unrealized_pnl(self, current_spread: float) -> float:
        if self._position == Position.FLAT:
            return 0.0
        direction = 1 if self._position == Position.LONG else -1
        return direction * (current_spread - self._entry_spread)

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        self._step_idx = 0
        self._position = Position.FLAT
        self._entry_spread = 0.0
        self._holding_steps = 0
        return self._get_obs(), {}

    def step(self, action: int):
        row = self.df.iloc[self._step_idx]
        current_spread = row["spread"]
        reward = 0.0
        terminated = False

        act = Action(action)

        if act == Action.ENTER_LONG and self._position == Position.FLAT:
            self._position = Position.LONG
            self._entry_spread = current_spread
            self._holding_steps = 0
            reward -= self.fee_rate
        elif act == Action.ENTER_SHORT and self._position == Position.FLAT:
            self._position = Position.SHORT
            self._entry_spread = current_spread
            self._holding_steps = 0
            reward -= self.fee_rate
        elif act == Action.EXIT and self._position != Position.FLAT:
            reward += self._unrealized_pnl(current_spread) - self.fee_rate
            self._position = Position.FLAT
            self._entry_spread = 0.0
            self._holding_steps = 0
        elif self._position != Position.FLAT:
            self._holding_steps += 1
            if self._holding_steps >= self.max_holding_steps:
                reward += self._unrealized_pnl(current_spread) - self.fee_rate
                self._position = Position.FLAT
                self._entry_spread = 0.0
                self._holding_steps = 0

        self._step_idx += 1
        truncated = self._step_idx >= len(self.df) - 1
        if truncated and self._position != Position.FLAT:
            reward += self._unrealized_pnl(current_spread) - self.fee_rate

        obs = self._get_obs() if not truncated else np.zeros(5, dtype=np.float32)
        return obs, reward, terminated, truncated, {}
