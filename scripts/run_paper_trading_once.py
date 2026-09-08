"""페이퍼 트레이딩을 1회 실행한다. GitHub Actions cron이 1시간마다 이 스크립트를 호출한다.

실제 주문은 나가지 않는다(PaperBroker 기반 시뮬레이션, 업비트 공개 시세 API만 사용).
"""
from __future__ import annotations

import asyncio
import logging

from upbit_spread_rl.agents.paper_run import run_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("paper_trading_once")


if __name__ == "__main__":
    result = asyncio.run(run_all())
    logger.info("페이퍼 트레이딩 실행 완료: %s", result)
