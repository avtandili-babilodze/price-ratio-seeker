"""Fetch historical prices from Yahoo Finance via yfinance."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import pandas as pd
import yfinance as yf


@dataclass
class PriceHistory:
    """Closing prices of one ticker over time."""

    ticker: str
    close: pd.Series  # DatetimeIndex -> price

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
        return PriceHistory(self.ticker, (self.close / self.first - 1.0) * 100.0)


def fetch_history(tickers, period, interval):
    """Fetch closing prices for each ticker, in parallel.

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
            return PriceHistory(ticker, close.dropna()), None
        except Exception as exc:
            return None, f"{ticker}: {exc}"

    histories, errors = [], []
    if not tickers:
        return histories, errors
    with ThreadPoolExecutor(max_workers=min(len(tickers), 8)) as pool:
        for history, error in pool.map(fetch_one, tickers):
            if history is not None:
                histories.append(history)
            else:
                errors.append(error)
    return histories, errors
