"""Fetch historical prices from Yahoo Finance via yfinance."""

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


def fetch_history(tickers, period, interval):
    """Fetch closing prices for each ticker.

    Returns (histories, errors): a list of PriceHistory for the tickers
    that resolved, and a list of human-readable error strings for the
    ones that did not. Never raises for a bad symbol or network hiccup.
    """
    histories, errors = [], []
    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(period=period, interval=interval)
            close = hist.get("Close")
            if close is None or close.dropna().empty:
                errors.append(f"{ticker}: no data (bad symbol?)")
            else:
                histories.append(PriceHistory(ticker, close.dropna()))
        except Exception as exc:
            errors.append(f"{ticker}: {exc}")
    return histories, errors
