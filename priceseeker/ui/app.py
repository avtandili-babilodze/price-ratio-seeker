"""Main window: toolbar (tickers, period buttons), chart, status bar.

Data fetching runs on a background thread so the window never freezes;
stale responses are discarded if a newer fetch was started meanwhile.
"""

import threading
import tkinter as tk
from tkinter import ttk

from .. import config, theme
from ..data import fetch_history
from .chart import ChartPanel


class StockViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Stock Price Viewer")
        self.geometry("1000x640")
        self.configure(bg=theme.PAGE)

        self.period_label = config.DEFAULT_PERIOD
        self.fetch_seq = 0  # ignore stale responses from superseded fetches

        self._build_toolbar()
        self.chart = ChartPanel(self)
        self.chart.widget.pack(fill="both", expand=True, padx=12, pady=0)
        self.chart.show_message("Enter a ticker and press Fetch")
        self._build_statusbar()

        self.entry.insert(0, config.DEFAULT_TICKER)
        self.after(100, self.fetch)

    # ---------- UI construction ----------

    def _build_toolbar(self):
        bar = tk.Frame(self, bg=theme.PAGE)
        bar.pack(fill="x", padx=12, pady=(12, 6))

        tk.Label(bar, text="Ticker(s)", bg=theme.PAGE,
                 fg=theme.INK_SECONDARY).pack(side="left")
        self.entry = tk.Entry(bar, width=28, fg=theme.INK_PRIMARY,
                              bg=theme.SURFACE, relief="solid", bd=1,
                              highlightthickness=0,
                              insertbackground=theme.INK_PRIMARY)
        self.entry.pack(side="left", padx=(8, 8), ipady=3)
        self.entry.bind("<Return>", lambda e: self.fetch())

        ttk.Button(bar, text="Fetch", command=self.fetch).pack(side="left")

        self.period_buttons = {}
        pframe = tk.Frame(bar, bg=theme.PAGE)
        pframe.pack(side="right")
        for label, _ in config.PERIODS:
            b = tk.Button(pframe, text=label, width=4, relief="flat", bd=0,
                          bg=theme.PAGE, fg=theme.INK_SECONDARY,
                          activebackground=theme.GRIDLINE,
                          command=lambda l=label: self.set_period(l))
            b.pack(side="left", padx=1)
            self.period_buttons[label] = b
        self._highlight_period()

    def _build_statusbar(self):
        self.status = tk.Label(self, text="", anchor="w",
                               bg=theme.PAGE, fg=theme.INK_MUTED)
        self.status.pack(fill="x", padx=12, pady=(2, 8))

    # ---------- Actions ----------

    def set_period(self, label):
        self.period_label = label
        self._highlight_period()
        self.fetch()

    def _highlight_period(self):
        for label, b in self.period_buttons.items():
            active = label == self.period_label
            b.configure(fg=theme.INK_PRIMARY if active else theme.INK_SECONDARY,
                        bg=theme.GRIDLINE if active else theme.PAGE,
                        font=("TkDefaultFont", 9, "bold" if active else "normal"))

    def fetch(self):
        tickers = [t.strip().upper()
                   for t in self.entry.get().split(",") if t.strip()]
        if not tickers:
            self.status.configure(text="Enter at least one ticker symbol.")
            return
        if len(tickers) > config.MAX_TICKERS:
            self.status.configure(
                text=f"Showing the first {config.MAX_TICKERS} tickers only.")
            tickers = tickers[:config.MAX_TICKERS]
        else:
            self.status.configure(text=f"Fetching {', '.join(tickers)}…")

        self.fetch_seq += 1
        seq = self.fetch_seq
        period, interval = dict(config.PERIODS)[self.period_label]
        threading.Thread(target=self._fetch_worker,
                         args=(seq, tickers, period, interval),
                         daemon=True).start()

    def _fetch_worker(self, seq, tickers, period, interval):
        histories, errors = fetch_history(tickers, period, interval)
        self.after(0, lambda: self._on_fetched(seq, histories, errors))

    def _on_fetched(self, seq, histories, errors):
        if seq != self.fetch_seq:
            return  # a newer fetch superseded this one
        if histories:
            colored = [(h, theme.SERIES[i]) for i, h in enumerate(histories)]
            self.chart.plot(colored, title=self._title(histories))
        if errors:
            self.status.configure(text=" | ".join(errors))
        elif histories:
            self.status.configure(
                text=f"Loaded {', '.join(h.ticker for h in histories)} "
                     f"({self.period_label}). Hover the chart for values.")

    def _title(self, histories):
        if len(histories) > 1:
            return " vs ".join(h.ticker for h in histories)
        h = histories[0]
        return (f"{h.ticker}  {h.last:,.2f}  "
                f"({h.change_pct:+.2f}% over {self.period_label})")
