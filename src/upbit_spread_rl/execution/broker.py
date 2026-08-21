"""Broker 인터페이스. PaperBroker/LiveBroker가 동일하게 구현해, 정책 코드는 어느 쪽인지 몰라도 되게 한다."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

Side = Literal["bid", "ask"]


@dataclass
class Order:
    market: str
    side: Side
    price: float
    volume: float
    order_id: str = ""


@dataclass
class Balance:
    currency: str
    amount: float
    locked: float = 0.0


class Broker(Protocol):
    async def get_balance(self, currency: str) -> Balance: ...

    async def place_order(self, order: Order) -> Order: ...

    async def cancel_order(self, order_id: str) -> None: ...

    async def get_open_orders(self, market: str) -> list[Order]: ...
