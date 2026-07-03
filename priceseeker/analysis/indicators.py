"""Classic technical indicators as pure pandas transforms.

Every function takes a closing-price Series (DatetimeIndex -> price) and
returns Series aligned to the same index, NaN until the window fills.
Windows are measured in bars, not days — the caller picks values that
make sense for its sampling interval.
"""

import pandas as pd


def sma(close: pd.Series, window: int) -> pd.Series:
    """Simple moving average."""
    return close.rolling(window).mean()


def ema(close: pd.Series, span: int) -> pd.Series:
    """Exponential moving average."""
    return close.ewm(span=span, adjust=False).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's Relative Strength Index, 0-100.

    Readings above 70 are conventionally "overbought", below 30
    "oversold". Perfectly flat stretches (no gains, no losses) yield
    NaN gaps, which plots simply skip.
    """
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False,
                                   min_periods=period).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False,
                                      min_periods=period).mean()
    return 100 - 100 / (1 + gain / loss)


def bollinger(close: pd.Series, window: int = 20, num_std: float = 2.0):
    """Bollinger bands: (middle, upper, lower).

    Middle is the SMA over `window`; the bands sit `num_std` rolling
    standard deviations away, so their width tracks recent volatility.
    """
    mid = close.rolling(window).mean()
    std = close.rolling(window).std()
    return mid, mid + num_std * std, mid - num_std * std
