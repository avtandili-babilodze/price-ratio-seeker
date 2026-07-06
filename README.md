# Stock Price Viewer

Desktop app that fetches stock prices from Yahoo Finance and plots
price-over-time in a window.

## Run

- **Linux / macOS:** `./run.sh`
- **Windows:** double-click `run.bat`

Both create a local `.venv` and install the dependencies automatically on
first run, then start the app.

Manual setup, if you prefer:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

## Project structure

```
main.py                  entry point
priceseeker/
├── config.py            app settings: periods, default ticker, limits, indicator windows
├── session.py           remembers toolbar state between runs (~/.config/priceseeker.json)
├── theme.py             all colors in one place
├── data/
│   ├── fetcher.py       Yahoo Finance access + in-memory cache (PriceHistory, fetch_history)
│   └── search.py        ticker name/symbol lookup (search_symbols)
├── analysis/
│   └── indicators.py    SMA, EMA, RSI, Bollinger bands
└── ui/
    ├── app.py           window, toolbar, status bar, background fetching
    ├── chart.py         chart panel: plotting, indicator overlays, hover crosshair/tooltip
    └── suggest.py       floating dropdown for ticker search suggestions
```

`data/` and `analysis/` are UI-free by design: new evaluators consume
`PriceHistory` objects and return plain results, and only `ui/` decides
how to display them.

## Usage

- Type a ticker (e.g. `AAPL`) or a company name (e.g. `google`) and press
  **Fetch** or Enter. As you type, a dropdown suggests matching symbols —
  pick one with the mouse, or arrow down and Enter.
- Compare stocks with a comma-separated list: `AAPL, MSFT, GOOG` (up to 8).
- Toggle **%** to rebase every line to percent change from the start of
  the window — the way to compare stocks whose prices differ wildly.
- Toggle **Log** for a log-scale price axis (price mode only) — long
  ranges like 5Y/Max stop exaggerating recent moves.
- Pick a time range with the buttons on the right: 1D, 5D, 1M, 6M, 1Y, 5Y, Max.
  Recently fetched data is cached for a minute, so flipping between
  periods is instant; the 1D view auto-refreshes every minute to stay live.
- Hover the chart for a crosshair with exact date and prices.
- Toggle technical indicators for a single-ticker chart (hidden when
  comparing multiple tickers):
  - **SMA 50 / EMA 20** — moving averages showing trend direction.
  - **Bands** — Bollinger bands showing recent volatility.
  - **RSI** — momentum oscillator (0–100) in its own sub-panel, with
    30/70 overbought/oversold guide lines.
  - **Vol** — traded volume as bars in its own sub-panel.

  These describe past price behavior; they don't predict future prices.
- **File → Save chart as PNG… / Export data as CSV…** share what's on
  screen (the CSV holds the raw closing prices of the plotted tickers).
- Keyboard: **Ctrl+S** save PNG, **Ctrl+E** export CSV, **Ctrl+L** jump
  to the ticker box, **Ctrl+Q** quit.
- The app reopens with the tickers, period, toggles and window size you
  last used.
