"""페어 스프레드(로그가격 비율의 평균회귀) 피처 계산."""
from __future__ import annotations

import numpy as np
import pandas as pd


def rolling_hedge_ratio(log_price_a: pd.Series, log_price_b: pd.Series, window: int = 240) -> pd.Series:
    """롤링 OLS로 beta(헤지비율)를 추정: log_price_a ~ beta * log_price_b."""
    cov = log_price_a.rolling(window).cov(log_price_b)
    var = log_price_b.rolling(window).var()
    return cov / var


def compute_spread(
    price_a: pd.Series, price_b: pd.Series, window: int = 240
) -> pd.DataFrame:
    """두 코인 가격 시계열로부터 스프레드와 z-score를 계산.

    Args:
        price_a, price_b: 종가 시계열(같은 인덱스, 시간 정렬됨).
        window: 헤지비율/z-score 롤링 윈도우(캔들 개수 기준).
    """
    log_a = np.log(price_a)
    log_b = np.log(price_b)
    beta = rolling_hedge_ratio(log_a, log_b, window)
    spread = log_a - beta * log_b

    spread_mean = spread.rolling(window).mean()
    spread_std = spread.rolling(window).std()
    zscore = (spread - spread_mean) / spread_std

    return pd.DataFrame(
        {
            "beta": beta,
            "spread": spread,
            "spread_zscore": zscore,
            "spread_change": spread.diff(),
        }
    )
