"""실시간 데이터 기반 모의 체결 브로커. 실거래 전 페이퍼 트레이딩 단계에서 사용."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from upbit_spread_rl.execution.broker import Balance, Order


@dataclass
class PaperBroker:
    fee_rate: float = 0.0005
    balances: dict[str, float] = field(default_factory=lambda: {"KRW": 1_000_000.0})
    _open_orders: dict[str, Order] = field(default_factory=dict)

    async def get_balance(self, currency: str) -> Balance:
        return Balance(currency=currency, amount=self.balances.get(currency, 0.0))

    async def place_order(self, order: Order) -> Order:
        order.order_id = order.order_id or uuid.uuid4().hex
        self._open_orders[order.order_id] = order
        return order

    async def cancel_order(self, order_id: str) -> None:
        self._open_orders.pop(order_id, None)

    async def get_open_orders(self, market: str) -> list[Order]:
        return [o for o in self._open_orders.values() if o.market == market]

    def fill_order(self, order_id: str) -> None:
        """오더북 시뮬레이션 결과 체결됐다고 판단될 때 외부(env/backtest 루프)에서 호출."""
        order = self._open_orders.pop(order_id, None)
        if order is None:
            return
        notional = order.price * order.volume
        fee = notional * self.fee_rate
        coin = order.market.split("-")[1]
        if order.side == "bid":
            self.balances["KRW"] = self.balances.get("KRW", 0.0) - notional - fee
            self.balances[coin] = self.balances.get(coin, 0.0) + order.volume
        else:
            self.balances["KRW"] = self.balances.get("KRW", 0.0) + notional - fee
            self.balances[coin] = self.balances.get(coin, 0.0) - order.volume
