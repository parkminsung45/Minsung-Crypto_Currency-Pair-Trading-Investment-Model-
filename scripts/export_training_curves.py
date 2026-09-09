"""학습 시 남긴 monitor.csv(에피소드별 보상)를 대시보드가 읽을 JSON으로 변환한다.

사용: python scripts/export_training_curves.py
(각 페어를 학습할 때마다 재실행해 dashboard/data/training_curves.json을 갱신한다.)
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from upbit_spread_rl.agents.paper_run import DEFAULT_PAIRS
from upbit_spread_rl.utils.config import PROJECT_ROOT

LOGS_DIR = PROJECT_ROOT / "logs"
OUT_PATH = PROJECT_ROOT / "dashboard" / "data" / "training_curves.json"


def _read_monitor_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        next(f)  # SB3 Monitor가 첫 줄에 JSON 메타데이터를 남긴다
        reader = csv.DictReader(f)
        return [
            {"episode": i + 1, "reward": float(row["r"]), "length": int(row["l"])}
            for i, row in enumerate(reader)
        ]


def main() -> None:
    curves = {}
    for market_a, market_b in DEFAULT_PAIRS:
        tag = f"{market_a}_{market_b}"
        path = LOGS_DIR / f"train_monitor_{tag}.csv.monitor.csv"
        if not path.exists():
            continue
        symbol_a, symbol_b = market_a.split("-")[1], market_b.split("-")[1]
        curves[f"{symbol_a}/{symbol_b}"] = _read_monitor_csv(path)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(curves, f, ensure_ascii=False, indent=2)
    print(f"{len(curves)}개 페어의 학습 곡선을 {OUT_PATH}에 저장했습니다.")


if __name__ == "__main__":
    main()
