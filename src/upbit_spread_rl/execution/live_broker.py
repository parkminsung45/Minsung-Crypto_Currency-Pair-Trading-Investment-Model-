"""업비트 Open API 실주문 브로커. JWT 인증 필요 (UPBIT_ACCESS_KEY/UPBIT_SECRET_KEY).

주의: 이 모듈은 실거래를 발생시킬 수 있다. RiskGuard 없이 직접 호출하지 말 것.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
import jwt

from upbit_spread_rl.execution.broker import Balance, Order
from upbit_spread_rl.utils.config import UpbitCredentials

UPBIT_REST_BASE = "https://api.upbit.com/v1"


@dataclass
class LiveBroker:
    credentials: UpbitCredentials
    client: httpx.AsyncClient

    def _auth_headers(self, query: dict | None = None) -> dict[str, str]:
        payload = {"access_key": self.credentials.access_key, "nonce": str(uuid.uuid4())}
        if query:
            query_string = urlencode(query)
            payload["query_hash"] = hashlib.sha512(query_string.encode()).hexdigest()
            payload["query_hash_alg"] = "SHA512"
        token = jwt.encode(payload, self.credentials.secret_key)
        return {"Authorization": f"Bearer {token}"}

    async def get_balance(self, currency: str) -> Balance:
        resp = await self.client.get(
            f"{UPBIT_REST_BASE}/accounts", headers=self._auth_headers()
        )
        resp.raise_for_status()
        for row in resp.json():
            if row["currency"] == currency:
                return Balance(
                    currency=currency,
                    amount=float(row["balance"]),
                    locked=float(row["locked"]),
                )
        return Balance(currency=currency, amount=0.0)

    async def place_order(self, order: Order) -> Order:
        query = {
            "market": order.market,
            "side": "bid" if order.side == "bid" else "ask",
            "volume": str(order.volume),
            "price": str(order.price),
            "ord_type": "limit",
        }
        resp = await self.client.post(
            f"{UPBIT_REST_BASE}/orders",
            params=query,
            headers=self._auth_headers(query),
        )
        resp.raise_for_status()
        body = resp.json()
        order.order_id = body["uuid"]
        return order

    async def cancel_order(self, order_id: str) -> None:
        query = {"uuid": order_id}
        resp = await self.client.delete(
            f"{UPBIT_REST_BASE}/order",
            params=query,
            headers=self._auth_headers(query),
        )
        resp.raise_for_status()

    async def get_open_orders(self, market: str) -> list[Order]:
        query = {"market": market, "state": "wait"}
        resp = await self.client.get(
            f"{UPBIT_REST_BASE}/orders", params=query, headers=self._auth_headers(query)
        )
        resp.raise_for_status()
        return [
            Order(
                market=row["market"],
                side=row["side"],
                price=float(row["price"]),
                volume=float(row["volume"]),
                order_id=row["uuid"],
            )
            for row in resp.json()
        ]
