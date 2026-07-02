"""Analysis of price histories: evaluators, trends, recommendations.

This package is the home for future features, e.g.:

    regression.py    linear-regression trend evaluators over PriceHistory
    suggestions.py   ranking / top-stock suggestions built on evaluators

Modules here consume `priceseeker.data.PriceHistory` objects and must not
import tkinter or matplotlib — return plain results (numbers, dataclasses,
pandas objects) and let `priceseeker.ui` decide how to display them.
"""
