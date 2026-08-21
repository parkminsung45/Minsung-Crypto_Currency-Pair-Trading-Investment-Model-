"""업비트 WebSocket으로 오더북/체결을 실시간 구독하고 콜백으로 전달한다.

업비트 WS는 유휴 연결을 일정 시간 뒤 끊으므로 재연결/백오프를 필수로 둔다.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

import websockets
from tenacity import retry, retry_if_exception_type, stop_never, wait_exponential

UPBIT_WS_URL = "wss://api.upbit.com/websocket/v1"

logger = logging.getLogger(__name__)

MessageHandler = Callable[[dict[str, Any]], Awaitable[None]]


class UpbitOrderbookStream:
    def __init__(
        self,
        markets: list[str],
        on_message: MessageHandler,
        types: tuple[str, ...] = ("orderbook", "trade"),
    ) -> None:
        self.markets = markets
        self.on_message = on_message
        self.types = types

    def _build_subscribe_payload(self) -> str:
        payload = [
            {"ticket": f"upbit-spread-rl-{uuid.uuid4().hex[:8]}"},
            *[{"type": t, "codes": self.markets} for t in self.types],
            {"format": "DEFAULT"},
        ]
        return json.dumps(payload)

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=60),
        stop=stop_never,
        retry=retry_if_exception_type(
            (websockets.exceptions.ConnectionClosed, OSError, asyncio.TimeoutError)
        ),
    )
    async def run(self) -> None:
        logger.info("connecting to upbit websocket for markets=%s", self.markets)
        async with websockets.connect(UPBIT_WS_URL, ping_interval=60) as ws:
            await ws.send(self._build_subscribe_payload())
            async for raw in ws:
                data = json.loads(raw)
                await self.on_message(data)
