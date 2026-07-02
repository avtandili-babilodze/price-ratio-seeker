"""Market data access. Everything here is UI-free and safe to use from
scripts, tests, or the analysis package."""

from .fetcher import PriceHistory, fetch_history

__all__ = ["PriceHistory", "fetch_history"]
