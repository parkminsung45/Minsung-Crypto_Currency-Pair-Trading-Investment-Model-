"""업비트 과거 분봉을 수집해 data/raw에 저장한다.

사용: python scripts/collect_candles.py --market KRW-BTC --days 30
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt

import httpx

from upbit_spread_rl.data.candle_fetcher import CandleFetcher
from upbit_spread_rl.data.storage import save_candles


async def main(market: str, days: int, unit_minutes: int) -> None:
    end = dt.datetime.now(dt.timezone.utc)
    start = end - dt.timedelta(days=days)

    fetcher = CandleFetcher(unit_minutes=unit_minutes)
    async with httpx.AsyncClient(timeout=10.0) as client:
        df = await fetcher.fetch_range(market, start, end, client)

    if df.empty:
        print(f"{market}: 수집된 데이터 없음")
        return

    for date, group in df.groupby(df["timestamp"].dt.date):
        save_candles(group, market, str(date))

    print(f"{market}: {len(df)}개 캔들 수집 완료 ({start.date()} ~ {end.date()})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", default="KRW-BTC")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--unit-minutes", type=int, default=1)
    args = parser.parse_args()

    asyncio.run(main(args.market, args.days, args.unit_minutes))
