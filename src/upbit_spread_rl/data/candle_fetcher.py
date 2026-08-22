"""업비트 REST API로 과거 분봉 캔들을 백필한다.

업비트 캔들 API는 `to` 파라미터 기준 과거로 최대 200개씩 페이지네이션된다.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import httpx
import pandas as pd
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from upbit_spread_rl.utils.rate_limiter import TokenBucketLimiter

UPBIT_REST_BASE = "https://api.upbit.com/v1"
MAX_CANDLES_PER_REQUEST = 200


def _is_rate_limited(exc: BaseException) -> bool:
    return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429


@dataclass
class CandleFetcher:
    unit_minutes: int = 1
    rate_limiter: TokenBucketLimiter | None = None

    def __post_init__(self) -> None:
        if self.rate_limiter is None:
            self.rate_limiter = TokenBucketLimiter(rate_per_sec=3.0, burst=3)

    @retry(
        retry=retry_if_exception(_is_rate_limited),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(6),
        reraise=True,
    )
    async def _get(self, client: httpx.AsyncClient, url: str, params: dict) -> httpx.Response:
        await self.rate_limiter.acquire()
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp

    async def fetch_range(
        self,
        market: str,
        start: dt.datetime,
        end: dt.datetime,
        client: httpx.AsyncClient,
    ) -> pd.DataFrame:
        """[start, end) 구간의 분봉을 최신→과거 페이지네이션으로 모두 수집해 시간순 DataFrame으로 반환."""
        rows: list[dict] = []
        cursor = end

        while cursor > start:
            params = {
                "market": market,
                "count": MAX_CANDLES_PER_REQUEST,
                "to": cursor.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            resp = await self._get(
                client, f"{UPBIT_REST_BASE}/candles/minutes/{self.unit_minutes}", params
            )
            batch = resp.json()
            if not batch:
                break

            rows.extend(batch)
            oldest = min(
                dt.datetime.fromisoformat(c["candle_date_time_utc"]).replace(tzinfo=dt.timezone.utc)
                for c in batch
            )
            if oldest >= cursor:
                break
            cursor = oldest

        if not rows:
            return pd.DataFrame(
                columns=["market", "timestamp", "open", "high", "low", "close", "volume"]
            )

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["candle_date_time_utc"], utc=True)
        df = df.rename(
            columns={
                "opening_price": "open",
                "high_price": "high",
                "low_price": "low",
                "trade_price": "close",
                "candle_acc_trade_volume": "volume",
            }
        )
        df = df[["market", "timestamp", "open", "high", "low", "close", "volume"]]
        df = df[(df["timestamp"] >= start) & (df["timestamp"] < end)]
        df = df.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)
        return df
