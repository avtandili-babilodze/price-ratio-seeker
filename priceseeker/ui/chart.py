"""Chart panel: a matplotlib price chart embedded in tkinter, with a
hover crosshair + tooltip layer and optional indicator overlays."""

import matplotlib

matplotlib.use("TkAgg")

import matplotlib.dates as mdates
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .. import theme


class ChartPanel:
    """Owns the embedded figure and everything drawn on it.

    plot() takes a list of (PriceHistory, color) pairs; the caller decides
    color assignment so it stays fixed per ticker. Indicators arrive
    pre-computed (this module does no analysis):
      overlays  [(label, Series, color)] drawn over the price axes
      bands     (mid, upper, lower) Series triple drawn as a shaded band
      rsi       Series on a 0-100 scale, shown in its own sub-panel
    """

    def __init__(self, master):
        self.fig = Figure(figsize=(9, 5), dpi=100, facecolor=theme.SURFACE)
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("figure_leave_event", lambda e: self._hide_hover())
        self.plotted = []  # [(PriceHistory, color)] currently on the axes
        self.ax = None
        self.ax_rsi = None
        self._rsi_series = None

    @property
    def widget(self):
        return self.canvas.get_tk_widget()

    def _layout(self, with_rsi):
        """Rebuild the axes; the RSI panel exists only when requested."""
        self.fig.clear()
        self.plotted = []
        self._rsi_series = None
        if with_rsi:
            gs = self.fig.add_gridspec(2, 1, height_ratios=(3, 1), hspace=0.10)
            self.ax = self.fig.add_subplot(gs[0])
            self.ax_rsi = self.fig.add_subplot(gs[1], sharex=self.ax)
            self.ax.tick_params(labelbottom=False)
        else:
            self.ax = self.fig.add_subplot(111)
            self.ax_rsi = None
        for ax in filter(None, (self.ax, self.ax_rsi)):
            self._style_axes(ax)
        self.fig.subplots_adjust(left=0.07, right=0.90, top=0.90, bottom=0.10)

    def show_message(self, text):
        self._layout(with_rsi=False)
        self.ax.set_title(text, color=theme.INK_SECONDARY, fontsize=11, loc="left")
        self.canvas.draw_idle()

    def plot(self, histories_with_colors, title, overlays=(), bands=None, rsi=None):
        self._layout(with_rsi=rsi is not None)
        ax = self.ax

        self.plotted = list(histories_with_colors)
        for history, color in self.plotted:
            ax.plot(history.close.index, history.close.values,
                    color=color, linewidth=2, label=history.ticker)
            # Direct label at the line's end instead of numbers on every point.
            ax.annotate(f" {history.ticker}  {history.last:,.2f}",
                        xy=(history.close.index[-1], history.last),
                        color=color, fontsize=9, fontweight="bold",
                        va="center", annotation_clip=False)

        if bands is not None:
            mid, upper, lower = bands
            ax.fill_between(mid.index, lower.values, upper.values,
                            color=theme.IND_BAND, alpha=0.13, linewidth=0,
                            label="Bollinger")
            ax.plot(mid.index, mid.values, color=theme.IND_BAND,
                    linewidth=1, linestyle="--")
        for label, series, color in overlays:
            ax.plot(series.index, series.values, color=color,
                    linewidth=1.3, label=label)

        if len(self.plotted) > 1 or overlays or bands is not None:
            ax.legend(loc="upper left", frameon=False, fontsize=9,
                      labelcolor=theme.INK_SECONDARY)
        ax.set_title(title, color=theme.INK_PRIMARY, fontsize=12,
                     fontweight="bold", loc="left", pad=12)
        ax.set_ylabel("Price", color=theme.INK_MUTED, fontsize=9)

        if rsi is not None:
            self._plot_rsi(rsi)

        bottom = self.ax_rsi if self.ax_rsi is not None else ax
        locator = mdates.AutoDateLocator()
        bottom.xaxis.set_major_locator(locator)
        bottom.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        ax.margins(x=0.02)

        # Hover layer: vertical crosshair + tooltip, hidden until first hover.
        # Anchor the crosshair inside the data range: axvline defaults to x=0,
        # which is 1970 in date units and would drag autoscale back to epoch.
        first_history = self.plotted[0][0]
        self._cursor = ax.axvline(x=first_history.close.index[0],
                                  color=theme.BASELINE, linewidth=0.8,
                                  visible=False)
        self._tooltip = ax.annotate(
            "", xy=(0, 0), xytext=(12, 12), textcoords="offset points",
            fontsize=9, color=theme.INK_PRIMARY, visible=False,
            bbox=dict(boxstyle="round,pad=0.4", fc=theme.SURFACE,
                      ec=theme.BASELINE, lw=0.8),
            zorder=10)
        self._dots = ax.scatter([], [], s=28, zorder=9,
                                edgecolors=theme.SURFACE, linewidths=1.5)
        self.canvas.draw_idle()

    def _plot_rsi(self, rsi):
        self._rsi_series = rsi
        r = self.ax_rsi
        r.plot(rsi.index, rsi.values, color=theme.IND_RSI, linewidth=1.3)
        for level in (30, 70):
            r.axhline(level, color=theme.BASELINE, linewidth=0.8,
                      linestyle="--")
        r.set_ylim(0, 100)
        r.set_yticks([30, 70])
        r.set_ylabel("RSI", color=theme.INK_MUTED, fontsize=9)
        r.margins(x=0.02)

    # ---------- Hover ----------

    @staticmethod
    def _nearest(series, when):
        """Index position of the sample closest to a hovered datetime."""
        idx = series.index.tz_localize(None) if series.index.tz else series.index
        return idx.get_indexer([when.replace(tzinfo=None)], method="nearest")[0]

    def _on_hover(self, event):
        if not self.plotted or event.inaxes != self.ax:
            self._hide_hover()
            return
        when = mdates.num2date(event.xdata)
        lines, xs, ys, colors = [], [], [], []
        for history, color in self.plotted:
            series = history.close
            pos = self._nearest(series, when)
            xs.append(mdates.date2num(series.index[pos]))
            y = float(series.iloc[pos])
            ys.append(y)
            colors.append(color)
            lines.append(f"{history.ticker}  {y:,.2f}")
        if self._rsi_series is not None:
            val = self._rsi_series.iloc[self._nearest(self._rsi_series, when)]
            if not np.isnan(val):
                lines.append(f"RSI  {val:.1f}")
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

    # ---------- Styling ----------

    def _style_axes(self, ax):
        ax.set_facecolor(theme.SURFACE)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(theme.BASELINE)
            ax.spines[side].set_linewidth(0.8)
        ax.tick_params(colors=theme.INK_MUTED, labelsize=9, length=3)
        ax.grid(True, axis="y", color=theme.GRIDLINE, linewidth=0.7)
        ax.set_axisbelow(True)
