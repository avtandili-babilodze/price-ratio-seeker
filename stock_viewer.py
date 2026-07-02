"""Stock price viewer.

Fetches historical prices from Yahoo Finance (via yfinance) and plots
price-over-time in a desktop window. Enter one ticker, or several separated
by commas to compare them on one chart.

Run:  python stock_viewer.py
"""

import threading
import tkinter as tk

import numpy as np
from tkinter import ttk

import matplotlib

matplotlib.use("TkAgg")

import matplotlib.dates as mdates
import yfinance as yf
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Palette (light surface)
SURFACE = "#fcfcfb"
PAGE = "#f9f9f7"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
# Categorical series colors, fixed assignment order (never cycled per-fetch:
# ticker N always gets slot N for the lifetime of one chart).
SERIES = ["#2a78d6", "#1baf7a", "#eda100", "#008300",
          "#4a3aa7", "#e34948", "#e87ba4", "#eb6834"]
MAX_TICKERS = len(SERIES)

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


class StockViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Stock Price Viewer")
        self.geometry("1000x640")
        self.configure(bg=PAGE)

        self.period_label = "6M"
        self.fetch_seq = 0  # ignore stale responses from superseded fetches
        self.plotted = []   # [(ticker, series, color)] currently on the axes

        self._build_toolbar()
        self._build_chart()
        self._build_statusbar()

        self.entry.insert(0, "AAPL")
        self.after(100, self.fetch)

    # ---------- UI construction ----------

    def _build_toolbar(self):
        bar = tk.Frame(self, bg=PAGE)
        bar.pack(fill="x", padx=12, pady=(12, 6))

        tk.Label(bar, text="Ticker(s)", bg=PAGE, fg=INK_SECONDARY).pack(side="left")
        self.entry = tk.Entry(bar, width=28, fg=INK_PRIMARY, bg=SURFACE,
                              relief="solid", bd=1,
                              highlightthickness=0, insertbackground=INK_PRIMARY)
        self.entry.pack(side="left", padx=(8, 8), ipady=3)
        self.entry.bind("<Return>", lambda e: self.fetch())

        ttk.Button(bar, text="Fetch", command=self.fetch).pack(side="left")

        self.period_buttons = {}
        pframe = tk.Frame(bar, bg=PAGE)
        pframe.pack(side="right")
        for label, _ in PERIODS:
            b = tk.Button(pframe, text=label, width=4, relief="flat", bd=0,
                          bg=PAGE, fg=INK_SECONDARY, activebackground=GRIDLINE,
                          command=lambda l=label: self.set_period(l))
            b.pack(side="left", padx=1)
            self.period_buttons[label] = b
        self._highlight_period()

    def _build_chart(self):
        self.fig = Figure(figsize=(9, 5), dpi=100, facecolor=SURFACE)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=0)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("figure_leave_event", lambda e: self._hide_hover())
        self._style_axes()
        self.ax.set_title("Enter a ticker and press Fetch",
                          color=INK_SECONDARY, fontsize=11, loc="left")
        self.canvas.draw_idle()

    def _build_statusbar(self):
        self.status = tk.Label(self, text="", anchor="w", bg=PAGE, fg=INK_MUTED)
        self.status.pack(fill="x", padx=12, pady=(2, 8))

    def _style_axes(self):
        ax = self.ax
        ax.set_facecolor(SURFACE)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(BASELINE)
            ax.spines[side].set_linewidth(0.8)
        ax.tick_params(colors=INK_MUTED, labelsize=9, length=3)
        ax.grid(True, axis="y", color=GRIDLINE, linewidth=0.7)
        ax.set_axisbelow(True)

    # ---------- Actions ----------

    def set_period(self, label):
        self.period_label = label
        self._highlight_period()
        self.fetch()

    def _highlight_period(self):
        for label, b in self.period_buttons.items():
            active = label == self.period_label
            b.configure(fg=INK_PRIMARY if active else INK_SECONDARY,
                        bg=GRIDLINE if active else PAGE,
                        font=("TkDefaultFont", 9, "bold" if active else "normal"))

    def fetch(self):
        tickers = [t.strip().upper() for t in self.entry.get().split(",") if t.strip()]
        if not tickers:
            self.status.configure(text="Enter at least one ticker symbol.")
            return
        if len(tickers) > MAX_TICKERS:
            self.status.configure(
                text=f"Showing the first {MAX_TICKERS} tickers only.")
            tickers = tickers[:MAX_TICKERS]
        else:
            self.status.configure(text=f"Fetching {', '.join(tickers)}…")

        self.fetch_seq += 1
        seq = self.fetch_seq
        period, interval = dict(PERIODS)[self.period_label]
        threading.Thread(target=self._fetch_worker,
                         args=(seq, tickers, period, interval),
                         daemon=True).start()

    def _fetch_worker(self, seq, tickers, period, interval):
        results, errors = [], []
        for ticker in tickers:
            try:
                hist = yf.Ticker(ticker).history(period=period, interval=interval)
                close = hist.get("Close")
                if close is None or close.dropna().empty:
                    errors.append(f"{ticker}: no data (bad symbol?)")
                else:
                    results.append((ticker, close.dropna()))
            except Exception as exc:
                errors.append(f"{ticker}: {exc}")
        self.after(0, lambda: self._on_fetched(seq, results, errors))

    def _on_fetched(self, seq, results, errors):
        if seq != self.fetch_seq:
            return  # a newer fetch superseded this one
        if results:
            self._plot(results)
        if errors:
            self.status.configure(text=" | ".join(errors))
        elif results:
            self.status.configure(
                text=f"Loaded {', '.join(t for t, _ in results)} "
                     f"({self.period_label}). Hover the chart for values.")

    # ---------- Plotting ----------

    def _plot(self, results):
        ax = self.ax
        ax.clear()
        self._style_axes()

        self.plotted = []
        for i, (ticker, series) in enumerate(results):
            color = SERIES[i]
            ax.plot(series.index, series.values, color=color, linewidth=2)
            self.plotted.append((ticker, series, color))
            # Direct label at the line's end instead of numbers on every point.
            last_x, last_y = series.index[-1], float(series.iloc[-1])
            ax.annotate(f" {ticker}  {last_y:,.2f}", xy=(last_x, last_y),
                        color=color, fontsize=9, fontweight="bold",
                        va="center", annotation_clip=False)

        if len(results) > 1:
            ax.legend([t for t, _, _ in self.plotted], loc="upper left",
                      frameon=False, fontsize=9, labelcolor=INK_SECONDARY)
            title = " vs ".join(t for t, _, _ in self.plotted)
        else:
            ticker, series, _ = self.plotted[0]
            first, last = float(series.iloc[0]), float(series.iloc[-1])
            pct = (last - first) / first * 100 if first else 0.0
            title = f"{ticker}  {last:,.2f}  ({pct:+.2f}% over {self.period_label})"
        ax.set_title(title, color=INK_PRIMARY, fontsize=12,
                     fontweight="bold", loc="left", pad=12)
        ax.set_ylabel("Price", color=INK_MUTED, fontsize=9)

        locator = mdates.AutoDateLocator()
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        ax.margins(x=0.02)
        self.fig.subplots_adjust(left=0.07, right=0.90, top=0.90, bottom=0.10)

        # Hover layer: vertical crosshair + tooltip, hidden until first hover.
        # Anchor the crosshair inside the data range: axvline defaults to x=0,
        # which is 1970 in date units and would drag autoscale back to epoch.
        self._cursor = ax.axvline(x=results[0][1].index[0], color=BASELINE,
                                  linewidth=0.8, visible=False)
        self._tooltip = ax.annotate(
            "", xy=(0, 0), xytext=(12, 12), textcoords="offset points",
            fontsize=9, color=INK_PRIMARY, visible=False,
            bbox=dict(boxstyle="round,pad=0.4", fc=SURFACE, ec=BASELINE, lw=0.8),
            zorder=10)
        self._dots = ax.scatter([], [], s=28, zorder=9,
                                edgecolors=SURFACE, linewidths=1.5)
        self.canvas.draw_idle()

    # ---------- Hover ----------

    def _on_hover(self, event):
        if not self.plotted or event.inaxes != self.ax:
            self._hide_hover()
            return
        when = mdates.num2date(event.xdata)
        lines, xs, ys, colors = [], [], [], []
        for ticker, series, color in self.plotted:
            idx = series.index.tz_localize(None) if series.index.tz else series.index
            pos = idx.get_indexer([when.replace(tzinfo=None)], method="nearest")[0]
            x, y = series.index[pos], float(series.iloc[pos])
            xs.append(mdates.date2num(x))
            ys.append(y)
            colors.append(color)
            lines.append(f"{ticker}  {y:,.2f}")
        stamp = xs[0]
        date_txt = mdates.num2date(stamp).strftime("%Y-%m-%d %H:%M")
        if date_txt.endswith("00:00"):
            date_txt = date_txt[:10]

        self._cursor.set_xdata([stamp, stamp])
        self._cursor.set_visible(True)
        self._dots.set_offsets(list(zip(xs, ys)))
        self._dots.set_facecolors(colors)
        self._tooltip.xy = (stamp, ys[0])
        self._tooltip.set_text(date_txt + "\n" + "\n".join(lines))
        self._tooltip.set_visible(True)
        self.canvas.draw_idle()

    def _hide_hover(self):
        if not self.plotted:
            return
        changed = self._cursor.get_visible() or self._tooltip.get_visible()
        self._cursor.set_visible(False)
        self._tooltip.set_visible(False)
        self._dots.set_offsets(np.empty((0, 2)))
        self._dots.set_facecolors([])
        if changed:
            self.canvas.draw_idle()


if __name__ == "__main__":
    StockViewer().mainloop()
