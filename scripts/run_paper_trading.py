"""1시간 단위 페이퍼 트레이딩 실행 진입점. launchd/cron이 매시간 호출한다.

사용자가 커밋을 신경 쓸 필요가 없도록, 실행 전 원격과 동기화하고 실행 후
커밋/푸시가 실패하면 pull --rebase 후 재시도까지 자동으로 처리한다.

사용: python scripts/run_paper_trading.py [--push]
"""
from __future__ import annotations

import argparse
import asyncio
import subprocess
import sys
import time
import traceback

from upbit_spread_rl.execution.runner import run_once
from upbit_spread_rl.utils.config import PROJECT_ROOT

TRACKED_PATHS = ["dashboard/data/history.json", "logs/paper_state.json"]
MAX_PUSH_ATTEMPTS = 3


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=PROJECT_ROOT, capture_output=True, text=True)


def _sync_before_run() -> None:
    """실행 전 로컬을 원격과 맞춘다. 이전 사이클에서 push에 실패해 로컬에만
    남은 커밋이 있어도 여기서 정리된다."""
    result = _run("git", "pull", "--rebase", "origin", "main")
    if result.returncode != 0:
        print(f"사전 동기화(pull --rebase) 실패, 그대로 진행: {result.stderr.strip()}")


def _commit_and_push() -> None:
    add = _run("git", "add", *TRACKED_PATHS)
    if add.returncode != 0:
        print(f"git add 실패 — 커밋 스킵: {add.stderr.strip()}")
        return

    if _run("git", "diff", "--cached", "--quiet").returncode == 0:
        print("변경 없음 — 커밋 스킵")
        return

    commit = _run("git", "commit", "-m", "페이퍼 트레이딩 실행 기록 갱신")
    if commit.returncode != 0:
        print(f"git commit 실패: {commit.stderr.strip()}")
        return

    for attempt in range(1, MAX_PUSH_ATTEMPTS + 1):
        push = _run("git", "push", "origin", "main")
        if push.returncode == 0:
            print(f"push 성공 (시도 {attempt}/{MAX_PUSH_ATTEMPTS})")
            return

        print(f"push 실패 (시도 {attempt}/{MAX_PUSH_ATTEMPTS}): {push.stderr.strip()}")
        if attempt == MAX_PUSH_ATTEMPTS:
            break

        # 원격이 앞서 있을 가능성 — rebase로 받아서 재시도. 리베이스 자체가
        # 실패하면(진짜 충돌) 다음 사이클에서 _sync_before_run이 다시 정리한다.
        rebase = _run("git", "pull", "--rebase", "origin", "main")
        if rebase.returncode != 0:
            print(f"push 재시도 전 rebase 실패, 중단: {rebase.stderr.strip()}")
            break
        time.sleep(2)

    print("push 최종 실패 — 로컬 커밋은 유지되며 다음 실행 시 자동 재시도됨")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--push", action="store_true", help="실행 후 기록을 커밋/푸시")
    args = parser.parse_args()

    if args.push:
        _sync_before_run()

    try:
        record = asyncio.run(run_once())
    except Exception:
        # 일시적 네트워크/API 오류로 이번 사이클이 실패해도 launchd 프로세스를
        # 비정상 종료시키지 않는다 — 다음 시간 주기에 자동으로 재시도된다.
        print("이번 사이클 실행 실패, 다음 주기에 자동 재시도됨:")
        traceback.print_exc()
        sys.exit(0)

    print(
        f"[{record['date']}] portfolio_value={record['portfolio_value']:.0f} "
        f"actions={record['actions']} weights={record['weights']}"
    )

    if args.push:
        _commit_and_push()


if __name__ == "__main__":
    main()
