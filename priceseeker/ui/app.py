"""Main window: toolbar (tickers, period buttons), chart, status bar.

Data fetching runs on a background thread so the window never freezes;
stale responses are discarded if a newer fetch was started meanwhile.
"""

import threading
import tkinter as tk
from tkinter import ttk

from .. import config, theme
from ..analysis import bollinger, ema, rsi, sma
from ..data import fetch_history, search_symbols
from .chart import ChartPanel
from .suggest import SuggestionDropdown


class StockViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Stock Price Viewer")
        self.geometry("1000x640")
        self.configure(bg=theme.PAGE)

        self.period_label = config.DEFAULT_PERIOD
        self.fetch_seq = 0  # ignore stale responses from superseded fetches
        self.suggest_seq = 0  # same idea for symbol-search lookups
        self._suggest_after = None  # pending debounce timer id
        self._last_entry_text = ""
        self.last_histories = []  # cached so indicator toggles replot offline

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

        self.suggest = SuggestionDropdown(self.entry, self._use_suggestion)
        self.entry.bind("<Return>", self._on_return)
        self.entry.bind("<KeyRelease>", self._on_entry_key)
        self.entry.bind("<Down>", lambda e: self.suggest.move(+1))
        self.entry.bind("<Up>", lambda e: self.suggest.move(-1))
        self.entry.bind("<Escape>", lambda e: self.suggest.hide())

        ttk.Button(bar, text="Fetch", command=self.fetch).pack(side="left")

        self.percent_var = self._add_toggle(bar, "%")
        self.indicator_vars = {
            key: self._add_toggle(bar, text)
            for key, text in (("sma", f"SMA {config.SMA_WINDOW}"),
                              ("ema", f"EMA {config.EMA_SPAN}"),
                              ("bands", "Bands"),
                              ("rsi", "RSI"))}

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

    def _add_toggle(self, bar, text):
        """A replot-on-click checkbox in the toolbar; returns its variable."""
        var = tk.BooleanVar(value=False)
        tk.Checkbutton(bar, text=text, variable=var, command=self._render,
                       bg=theme.PAGE, fg=theme.INK_SECONDARY,
                       activebackground=theme.PAGE,
                       activeforeground=theme.INK_PRIMARY,
                       selectcolor=theme.SURFACE,
                       highlightthickness=0).pack(side="left", padx=(8, 0))
        return var

    def _build_statusbar(self):
        self.status = tk.Label(self, text="", anchor="w",
                               bg=theme.PAGE, fg=theme.INK_MUTED)
        self.status.pack(fill="x", padx=12, pady=(2, 8))

    # ---------- Symbol suggestions ----------

    def _on_entry_key(self, event):
        text = self.entry.get()
        if text == self._last_entry_text:
            return  # navigation key, not an edit
        self._last_entry_text = text
        if self._suggest_after:
            self.after_cancel(self._suggest_after)
        self._suggest_after = self.after(config.SUGGEST_DELAY_MS,
                                         self._request_suggestions)

    def _request_suggestions(self):
        self._suggest_after = None
        # Only the segment after the last comma is being typed.
        query = self.entry.get().rsplit(",", 1)[-1].strip()
        if len(query) < 2:
            self.suggest.hide()
            return
        self.suggest_seq += 1
        threading.Thread(target=self._suggest_worker,
                         args=(self.suggest_seq, query),
                         daemon=True).start()

    def _suggest_worker(self, seq, query):
        results = search_symbols(query, limit=config.MAX_SUGGESTIONS)
        self.after(0, lambda: self._on_suggestions(seq, results))

    def _on_suggestions(self, seq, results):
        if seq != self.suggest_seq or self.focus_get() is not self.entry:
            return
        self.suggest.show(results)

    def _use_suggestion(self, symbol):
        parts = self.entry.get().rsplit(",", 1)
        prefix = parts[0] + ", " if len(parts) > 1 else ""
        self.entry.delete(0, "end")
        self.entry.insert(0, prefix + symbol)
        self._last_entry_text = self.entry.get()
        self.fetch()

    def _cancel_suggestions(self):
        if self._suggest_after:
            self.after_cancel(self._suggest_after)
            self._suggest_after = None
        self.suggest_seq += 1  # drop any lookup already in flight
        self.suggest.hide()

    def _on_return(self, event=None):
        if self.suggest.pick_active():
            return  # picking already triggers a fetch
        self.fetch()

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
        self._cancel_suggestions()
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
        if errors:
            self.status.configure(text=" | ".join(errors))
        elif histories:
            self.status.configure(
                text=f"Loaded {', '.join(h.ticker for h in histories)} "
                     f"({self.period_label}). Hover the chart for values.")
        if histories:
            self.last_histories = histories
            self._render()  # after status: its single-ticker hint may override

    def _render(self):
        """Redraw the chart from cached histories with current indicators."""
        histories = self.last_histories
        if not histories:
            return
        percent = self.percent_var.get()
        shown = [h.rebased() for h in histories] if percent else histories
        colored = [(h, theme.SERIES[i]) for i, h in enumerate(shown)]

        overlays, bands, rsi_series = [], None, None
        wanted = {k for k, v in self.indicator_vars.items() if v.get()}
        if wanted and len(histories) > 1:
            self.status.configure(
                text="Indicators are shown on single-ticker charts only.")
        elif wanted:
            # Rebasing is linear, so indicators of the rebased series equal
            # rebased indicators (and RSI is scale-invariant either way).
            close = shown[0].close
            if "sma" in wanted:
                overlays.append((f"SMA {config.SMA_WINDOW}",
                                 sma(close, config.SMA_WINDOW), theme.IND_SMA))
            if "ema" in wanted:
                overlays.append((f"EMA {config.EMA_SPAN}",
                                 ema(close, config.EMA_SPAN), theme.IND_EMA))
            if "bands" in wanted:
                bands = bollinger(close, config.BOLLINGER_WINDOW,
                                  config.BOLLINGER_STD)
            if "rsi" in wanted:
                rsi_series = rsi(close, config.RSI_PERIOD)

        self.chart.plot(colored, title=self._title(histories),
                        overlays=overlays, bands=bands, rsi=rsi_series,
                        percent=percent)

    def _title(self, histories):
        if len(histories) > 1:
            return " vs ".join(h.ticker for h in histories)
        h = histories[0]
        return (f"{h.ticker}  {h.last:,.2f}  "
                f"({h.change_pct:+.2f}% over {self.period_label})")
