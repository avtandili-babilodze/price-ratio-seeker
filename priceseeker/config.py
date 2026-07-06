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

# Fetching
CACHE_TTL_S = 60  # serve repeat requests from memory for this long
AUTO_REFRESH_1D_MS = 60_000  # the 1D view refetches this often to stay live

# Ticker search-as-you-type
SUGGEST_DELAY_MS = 300  # debounce between last keystroke and the lookup
MAX_SUGGESTIONS = 6

# Technical indicators (single-ticker charts only). Windows are in bars,
# not days: 50 bars is ~50 trading days on daily periods but ~4 hours
# on the 1D/5-minute view.
SMA_WINDOW = 50
EMA_SPAN = 20
BOLLINGER_WINDOW = 20
BOLLINGER_STD = 2.0
RSI_PERIOD = 14
