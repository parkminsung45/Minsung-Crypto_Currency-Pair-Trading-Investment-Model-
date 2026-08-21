"""호가 스프레드(마켓메이킹) Gymnasium 환경.

행동(연속): [bid_offset_bps, ask_offset_bps] — mid 대비 매수/매도 지정가 오프셋(bp 단위, >=0).
체결 가정: 다음 스텝의 best_bid/best_ask가 우리 호가를 지나치면 체결된 것으로 간주(단순화된 시뮬레이션).
재고 리스크: 재고가 inventory_cap을 넘으면 초과분에 페널티.
"""
from __future__ import annotations

import gymnasium as gym
import numpy as np
import pandas as pd
from gymnasium import spaces


class QuoteSpreadEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(
        self,
        features_df: pd.DataFrame,
        fee_rate: float = 0.0005,
        inventory_cap: float = 1.0,
        inventory_penalty_coef: float = 0.001,
        max_offset_bps: float = 50.0,
    ) -> None:
        """
        Args:
            features_df: quote_spread.compute_quote_features() 출력
                (컬럼: timestamp, mid_price, spread, spread_bps, order_imbalance).
            fee_rate: 체결 시 편도 수수료율.
            inventory_cap: 절대 재고 허용 한도(코인 수량 기준, 정규화된 단위).
            inventory_penalty_coef: 재고 한도 초과분에 대한 페널티 계수.
            max_offset_bps: 행동으로 낼 수 있는 최대 오프셋(bp).
        """
        super().__init__()
        required_cols = {"mid_price", "spread_bps", "order_imbalance"}
        missing = required_cols - set(features_df.columns)
        if missing:
            raise ValueError(f"features_df에 필요한 컬럼이 없습니다: {missing}")

        self.df = features_df.reset_index(drop=True)
        self.fee_rate = fee_rate
        self.inventory_cap = inventory_cap
        self.inventory_penalty_coef = inventory_penalty_coef
        self.max_offset_bps = max_offset_bps

        self.action_space = spaces.Box(
            low=np.array([0.0, 0.0], dtype=np.float32),
            high=np.array([max_offset_bps, max_offset_bps], dtype=np.float32),
        )
        # obs: [mid_price_change_bps, spread_bps, order_imbalance, inventory]
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(4,), dtype=np.float32
        )

        self._step_idx = 0
        self._inventory = 0.0
        self._cash = 0.0

    def _get_obs(self) -> np.ndarray:
        row = self.df.iloc[self._step_idx]
        prev_mid = self.df.iloc[max(self._step_idx - 1, 0)]["mid_price"]
        mid_change_bps = (row["mid_price"] - prev_mid) / prev_mid * 10_000 if prev_mid else 0.0
        return np.array(
            [mid_change_bps, row["spread_bps"], row["order_imbalance"], self._inventory],
            dtype=np.float32,
        )

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        self._step_idx = 0
        self._inventory = 0.0
        self._cash = 0.0
        return self._get_obs(), {}

    def step(self, action: np.ndarray):
        bid_offset_bps, ask_offset_bps = float(action[0]), float(action[1])
        row = self.df.iloc[self._step_idx]
        mid = row["mid_price"]

        our_bid = mid * (1 - bid_offset_bps / 10_000)
        our_ask = mid * (1 + ask_offset_bps / 10_000)

        next_idx = min(self._step_idx + 1, len(self.df) - 1)
        next_row = self.df.iloc[next_idx]
        next_mid = next_row["mid_price"]
        next_spread_half = next_row["spread_bps"] / 2 / 10_000 * next_mid
        next_best_bid = next_mid - next_spread_half
        next_best_ask = next_mid + next_spread_half

        reward = 0.0

        bid_filled = next_best_bid <= our_bid
        if bid_filled:
            self._inventory += 1.0
            self._cash -= our_bid * (1 + self.fee_rate)
            reward += (mid - our_bid) / mid * 10_000

        ask_filled = next_best_ask >= our_ask
        if ask_filled:
            self._inventory -= 1.0
            self._cash += our_ask * (1 - self.fee_rate)
            reward += (our_ask - mid) / mid * 10_000

        excess_inventory = max(abs(self._inventory) - self.inventory_cap, 0.0)
        reward -= self.inventory_penalty_coef * excess_inventory * 10_000

        self._step_idx += 1
        truncated = self._step_idx >= len(self.df) - 1
        terminated = False

        obs = self._get_obs() if not truncated else np.zeros(4, dtype=np.float32)
        info = {"inventory": self._inventory, "cash": self._cash}
        return obs, reward, terminated, truncated, info
