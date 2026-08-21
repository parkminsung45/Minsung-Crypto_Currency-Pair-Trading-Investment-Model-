"""실거래 진입 전 필수 게이트. 일일 손실 한도, 최대 포지션, 연속 손실 킬스위치."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field


class RiskLimitBreached(Exception):
    pass


@dataclass
class RiskGuard:
    daily_loss_limit_krw: float
    max_position_krw: float
    max_consecutive_losses: int = 5

    _daily_pnl: float = 0.0
    _consecutive_losses: int = 0
    _current_date: dt.date = field(default_factory=dt.date.today)
    _halted: bool = False

    def _roll_day_if_needed(self) -> None:
        today = dt.date.today()
        if today != self._current_date:
            self._current_date = today
            self._daily_pnl = 0.0
            self._consecutive_losses = 0
            self._halted = False

    def record_trade_pnl(self, pnl_krw: float) -> None:
        self._roll_day_if_needed()
        self._daily_pnl += pnl_krw
        if pnl_krw < 0:
            self._consecutive_losses += 1
        else:
            self._consecutive_losses = 0

        if self._daily_pnl <= -abs(self.daily_loss_limit_krw):
            self._halted = True
        if self._consecutive_losses >= self.max_consecutive_losses:
            self._halted = True

    def check_order_allowed(self, notional_krw: float) -> None:
        self._roll_day_if_needed()
        if self._halted:
            raise RiskLimitBreached(
                f"거래 중단됨: 일일손익={self._daily_pnl:.0f}, 연속손실={self._consecutive_losses}"
            )
        if notional_krw > self.max_position_krw:
            raise RiskLimitBreached(
                f"주문 규모({notional_krw:.0f})가 최대 허용치({self.max_position_krw:.0f})를 초과"
            )

    @property
    def is_halted(self) -> bool:
        self._roll_day_if_needed()
        return self._halted
