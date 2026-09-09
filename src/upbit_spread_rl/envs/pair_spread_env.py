"""페어 스프레드(통계적 차익거래) Gymnasium 환경.

행동: 0=유지/청산상태 유지, 1=롱 스프레드 진입, 2=숏 스프레드 진입, 3=청산
상태: [spread_zscore, spread_change, position, unrealized_pnl, holding_steps]
보상: 스텝별 미실현손익 변화(delta) - 진입/청산 시 수수료

min/max_holding_steps: scripts/diagnose_mean_reversion.py로 실측한 결과, z-score와
향후 스프레드 변화의 상관관계(평균회귀 신호)는 60분 이내에는 거의 0이고
120~480분 구간에서 뚜렷해진다(최대 corr -0.40). 그래서 진입 직후 곧바로 청산해
신호가 약한 구간에서 노이즈로 손익이 결정되는 것을 막기 위해 min_holding_steps로
조기 청산을 제한하고, 신호가 죽는 480분 이후까지 계속 들고 있지 않도록
max_holding_steps를 그 안쪽으로 잡는다.
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
        min_holding_steps: int = 120,
        max_holding_steps: int = 240,
    ) -> None:
        """
        Args:
            features_df: pair_spread.compute_spread() 출력 + 원본 가격 컬럼(price_a, price_b),
                NaN(워밍업 구간)은 미리 제거되어 있어야 한다.
            fee_rate: 편도 수수료율(진입/청산 각각 적용).
            min_holding_steps: 진입 후 이 스텝 수가 지나기 전에는 EXIT 액션을 무시한다
                (신호가 약한 구간에서 조기 청산으로 노이즈에 오버피팅되는 것을 방지).
            max_holding_steps: 포지션 강제 청산까지 최대 보유 스텝 수(신호가 죽는
                구간까지 계속 들고 있지 않도록 min_holding_steps보다 커야 한다).
        """
        super().__init__()
        required_cols = {"spread", "spread_zscore", "spread_change", "price_a", "price_b"}
        missing = required_cols - set(features_df.columns)
        if missing:
            raise ValueError(f"features_df에 필요한 컬럼이 없습니다: {missing}")
        if min_holding_steps >= max_holding_steps:
            raise ValueError("min_holding_steps는 max_holding_steps보다 작아야 합니다")

        self.df = features_df.reset_index(drop=True)
        self.fee_rate = fee_rate
        self.min_holding_steps = min_holding_steps
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
        self._prev_unrealized_pnl = 0.0
        return self._get_obs(), {}

    def step(self, action: int):
        row = self.df.iloc[self._step_idx]
        current_spread = row["spread"]
        reward = 0.0
        terminated = False

        act = Action(action)
        can_exit = self._position != Position.FLAT and self._holding_steps >= self.min_holding_steps

        if act == Action.ENTER_LONG and self._position == Position.FLAT:
            self._position = Position.LONG
            self._entry_spread = current_spread
            self._holding_steps = 0
            self._prev_unrealized_pnl = 0.0
            reward -= self.fee_rate
        elif act == Action.ENTER_SHORT and self._position == Position.FLAT:
            self._position = Position.SHORT
            self._entry_spread = current_spread
            self._holding_steps = 0
            self._prev_unrealized_pnl = 0.0
            reward -= self.fee_rate
        elif act == Action.EXIT and can_exit:
            reward += self._unrealized_pnl(current_spread) - self._prev_unrealized_pnl - self.fee_rate
            self._position = Position.FLAT
            self._entry_spread = 0.0
            self._holding_steps = 0
            self._prev_unrealized_pnl = 0.0
        elif self._position != Position.FLAT:
            # min_holding_steps 이전의 EXIT 시도를 포함해, 포지션을 유지하는 모든
            # 경우 스텝별 미실현손익 변화(delta)를 보상으로 준다 — 청산까지 기다리는
            # 대신 매 스텝 credit assignment가 되어 학습이 안정적이다.
            self._holding_steps += 1
            pnl_now = self._unrealized_pnl(current_spread)
            reward += pnl_now - self._prev_unrealized_pnl
            self._prev_unrealized_pnl = pnl_now
            if self._holding_steps >= self.max_holding_steps:
                reward -= self.fee_rate
                self._position = Position.FLAT
                self._entry_spread = 0.0
                self._holding_steps = 0
                self._prev_unrealized_pnl = 0.0

        self._step_idx += 1
        truncated = self._step_idx >= len(self.df) - 1
        if truncated and self._position != Position.FLAT:
            # 에피소드 끝에 열린 포지션이 있으면 강제 청산 — 이번 스텝 delta는 이미
            # 위에서 반영됐으므로 여기서는 청산 수수료만 추가로 부과한다.
            reward -= self.fee_rate

        obs = self._get_obs() if not truncated else np.zeros(5, dtype=np.float32)
        return obs, reward, terminated, truncated, {}
