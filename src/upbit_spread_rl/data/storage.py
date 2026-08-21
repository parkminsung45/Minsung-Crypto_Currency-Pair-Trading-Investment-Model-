"""Parquet 기반 데이터 저장소. raw/processed 2단계, 마켓·날짜별 파티셔닝."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from upbit_spread_rl.utils.config import PROJECT_ROOT

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def _partition_path(base_dir: Path, market: str, kind: str, date: str) -> Path:
    path = base_dir / kind / market / f"{date}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_candles(df: pd.DataFrame, market: str, date: str) -> Path:
    path = _partition_path(RAW_DIR, market, "candles", date)
    df.to_parquet(path, index=False)
    return path


def load_candles(market: str, date: str) -> pd.DataFrame:
    path = _partition_path(RAW_DIR, market, "candles", date)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def append_stream_batch(df: pd.DataFrame, market: str, kind: str, date: str) -> Path:
    """실시간 스트림(orderbook/trade) 배치를 같은 날짜 파티션에 이어붙인다."""
    path = _partition_path(RAW_DIR, market, kind, date)
    if path.exists():
        existing = pd.read_parquet(path)
        df = pd.concat([existing, df], ignore_index=True)
    df.to_parquet(path, index=False)
    return path
