"""1시간 단위 페이퍼 트레이딩 실행 진입점. launchd/cron이 매시간 호출한다.

사용: python scripts/run_paper_trading.py [--push]
"""
from __future__ import annotations

import argparse
import asyncio
import subprocess

from upbit_spread_rl.execution.runner import run_once
from upbit_spread_rl.utils.config import PROJECT_ROOT


def _git_commit_and_push() -> None:
    add = subprocess.run(
        ["git", "add", "dashboard/data/history.json", "logs/paper_state.json"], cwd=PROJECT_ROOT
    )
    if add.returncode != 0:
        print("git add 실패 — 커밋 스킵")
        return
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=PROJECT_ROOT)
    if diff.returncode == 0:
        print("변경 없음 — 커밋 스킵")
        return
    subprocess.run(
        ["git", "commit", "-m", "페이퍼 트레이딩 실행 기록 갱신"], cwd=PROJECT_ROOT, check=True
    )
    subprocess.run(["git", "push", "origin", "main"], cwd=PROJECT_ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--push", action="store_true", help="실행 후 기록을 커밋/푸시")
    args = parser.parse_args()

    record = asyncio.run(run_once())
    print(
        f"[{record['date']}] portfolio_value={record['portfolio_value']:.0f} "
        f"actions={record['actions']} weights={record['weights']}"
    )

    if args.push:
        _git_commit_and_push()


if __name__ == "__main__":
    main()
