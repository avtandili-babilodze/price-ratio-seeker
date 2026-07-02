"""App-level settings."""

from . import theme

# label -> (yfinance period, interval)
PERIODS = [
    ("1D", ("1d", "5m")),
    ("5D", ("5d", "30m")),
    ("1M", ("1mo", "1d")),
    ("6M", ("6mo", "1d")),
    ("1Y", ("1y", "1d")),
    ("5Y", ("5y", "1wk")),
    ("Max", ("max", "1mo")),
]

DEFAULT_PERIOD = "6M"
DEFAULT_TICKER = "AAPL"

# One chart can show at most one series per categorical color slot.
MAX_TICKERS = len(theme.SERIES)
