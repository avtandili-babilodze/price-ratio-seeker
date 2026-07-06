"""Fetch historical prices from Yahoo Finance via yfinance.

Results are cached in memory for a short time, so flipping between
periods (or re-fetching the same tickers) replots instantly instead of
re-downloading.
"""

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import pandas as pd
import yfinance as yf


@dataclass
class PriceHistory:
    """Closing prices (and traded volume, when available) of one ticker."""

    ticker: str
    close: pd.Series  # DatetimeIndex -> price
    volume: pd.Series | None = None  # aligned to close; None if feed had none

    @property
    def first(self) -> float:
        return float(self.close.iloc[0])

    @property
    def last(self) -> float:
        return float(self.close.iloc[-1])

    @property
    def change_pct(self) -> float:
        return (self.last - self.first) / self.first * 100 if self.first else 0.0

    def rebased(self) -> "PriceHistory":
        """This history as % change from its first sample (starts at 0)."""
        if not self.first:
            return self
        return PriceHistory(self.ticker, (self.close / self.first - 1.0) * 100.0,
                            self.volume)


_cache = {}  # (ticker, period, interval) -> (fetched_at, PriceHistory)


def fetch_history(tickers, period, interval, ttl=60.0, force=False):
    """Fetch closing prices for each ticker, in parallel.

    Results newer than `ttl` seconds are served from memory; force=True
    bypasses the cache (used by auto-refresh). Errors are never cached.
    Returns (histories, errors): a list of PriceHistory for the tickers
    that resolved — in input order, so color slots stay stable — and a
    list of human-readable error strings for the ones that did not.
    Never raises for a bad symbol or network hiccup.
    """
    def fetch_one(ticker):
        try:
            hist = yf.Ticker(ticker).history(period=period, interval=interval)
            close = hist.get("Close")
            if close is None or close.dropna().empty:
                return None, f"{ticker}: no data (bad symbol?)"
            close = close.dropna()
            volume = hist.get("Volume")
            if volume is not None:
                volume = volume.reindex(close.index).fillna(0.0)
            return PriceHistory(ticker, close, volume), None
        except Exception as exc:
            return None, f"{ticker}: {exc}"

    now = time.time()
    resolved = {}
    if not force:
        for ticker in tickers:
            hit = _cache.get((ticker, period, interval))
            if hit and now - hit[0] < ttl:
                resolved[ticker] = hit[1]
    misses = [t for t in tickers if t not in resolved]
    errors = []
    if misses:
        with ThreadPoolExecutor(max_workers=min(len(misses), 8)) as pool:
            for ticker, (history, error) in zip(misses,
                                                pool.map(fetch_one, misses)):
                if history is not None:
                    _cache[(ticker, period, interval)] = (now, history)
                    resolved[ticker] = history
                else:
                    errors.append(error)
    return [resolved[t] for t in tickers if t in resolved], errors
