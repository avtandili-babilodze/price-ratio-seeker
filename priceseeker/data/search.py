"""Resolve free-text queries ("google") to ticker symbols via Yahoo search."""

from dataclasses import dataclass

import yfinance as yf


@dataclass
class SymbolSuggestion:
    """One search hit: a tradable symbol plus display context."""

    symbol: str
    name: str
    exchange: str


def search_symbols(query, limit=8):
    """Best-effort symbol lookup for a company name or partial ticker.

    Returns a list of SymbolSuggestion, or [] on any failure — suggestions
    are a typing convenience and must never surface errors.
    """
    try:
        quotes = yf.Search(query, max_results=limit, news_count=0,
                           lists_count=0, include_cb=False,
                           enable_fuzzy_query=True).quotes
    except Exception:
        return []
    return [SymbolSuggestion(q["symbol"],
                             q.get("shortname") or q.get("longname") or "",
                             q.get("exchDisp") or q.get("exchange") or "")
            for q in quotes[:limit]]
