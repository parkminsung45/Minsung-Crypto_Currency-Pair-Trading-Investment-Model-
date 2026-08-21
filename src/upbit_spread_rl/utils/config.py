"""프로젝트 전역 설정. .env와 configs/*.yaml을 함께 읽는다."""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class UpbitCredentials(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="UPBIT_", extra="ignore")

    access_key: str = ""
    secret_key: str = ""


class RunSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    run_mode: str = "backtest"  # backtest | paper | live


class MarketConfig(BaseModel):
    pair_markets: list[str] = ["KRW-BTC", "KRW-ETH"]
    quote_market: str = "KRW-BTC"
    candle_unit_minutes: int = 1
    fee_rate: float = 0.0005  # 업비트 기본 수수료 0.05%


def load_market_config(path: str | Path | None = None) -> MarketConfig:
    path = Path(path) if path else PROJECT_ROOT / "configs" / "market.yaml"
    if not path.exists():
        return MarketConfig()
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return MarketConfig(**raw)
