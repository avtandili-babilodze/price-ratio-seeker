"""Analysis of price histories: evaluators, trends, recommendations.

Current modules:

    indicators.py    technical indicators (SMA, EMA, RSI, Bollinger)

Modules here consume `priceseeker.data.PriceHistory` objects and must not
import tkinter or matplotlib — return plain results (numbers, dataclasses,
pandas objects) and let `priceseeker.ui` decide how to display them.
"""

from .indicators import bollinger, ema, rsi, sma

__all__ = ["bollinger", "ema", "rsi", "sma"]
