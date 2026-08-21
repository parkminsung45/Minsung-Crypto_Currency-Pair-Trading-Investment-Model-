"""dashboard/index.html이 읽는 dashboard/data/history.json을 갱신한다.

레코드 스키마 (한 실행 = 한 레코드):
    {
        "date": "YYYY-MM-DD",
        "portfolio_value": float,          # KRW 평가액
        "daily_return_pct": float | null,  # 직전 기록 대비 %, 첫 기록은 null
        "weights": {"BTC": float, "ETH": float, "CASH": float},  # 합 1.0
        "actions": {"BTC": "HOLD"|"BUY"|"SELL", ...},
        "dry_run": bool,
    }
"""
from __future__ import annotations

import json
from pathlib import Path

from upbit_spread_rl.utils.config import PROJECT_ROOT

HISTORY_PATH = PROJECT_ROOT / "dashboard" / "data" / "history.json"


def load_history() -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    with open(HISTORY_PATH, encoding="utf-8") as f:
        return json.load(f)


def append_record(
    date: str,
    portfolio_value: float,
    weights: dict[str, float],
    actions: dict[str, str] | None = None,
    dry_run: bool = True,
) -> list[dict]:
    """새 실행 결과를 history.json에 append하고 저장한다. 같은 date가 이미 있으면 덮어쓴다."""
    history = load_history()
    history = [h for h in history if h["date"] != date]

    prev_value = history[-1]["portfolio_value"] if history else None
    daily_return_pct = (
        (portfolio_value / prev_value - 1) * 100 if prev_value else None
    )

    history.append(
        {
            "date": date,
            "portfolio_value": portfolio_value,
            "daily_return_pct": daily_return_pct,
            "weights": weights,
            "actions": actions or {},
            "dry_run": dry_run,
        }
    )
    history.sort(key=lambda h: h["date"])

    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return history
