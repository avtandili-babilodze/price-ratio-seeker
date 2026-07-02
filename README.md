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
.venv/bin/python stock_viewer.py
```

## Usage

- Type a ticker (e.g. `AAPL`) and press **Fetch** or Enter.
- Compare stocks with a comma-separated list: `AAPL, MSFT, GOOG` (up to 8).
- Pick a time range with the buttons on the right: 1D, 5D, 1M, 6M, 1Y, 5Y, Max.
- Hover the chart for a crosshair with exact date and prices.
