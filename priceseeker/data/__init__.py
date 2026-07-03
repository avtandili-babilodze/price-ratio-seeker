"""Market data access. Everything here is UI-free and safe to use from
scripts, tests, or the analysis package."""

from .fetcher import PriceHistory, fetch_history
from .search import SymbolSuggestion, search_symbols

__all__ = ["PriceHistory", "SymbolSuggestion", "fetch_history", "search_symbols"]
