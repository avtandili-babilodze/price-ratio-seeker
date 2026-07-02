"""Chart panel: a matplotlib price chart embedded in tkinter, with a
hover crosshair + tooltip layer."""

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
    color assignment so it stays fixed per ticker.
    """

    def __init__(self, master):
        self.fig = Figure(figsize=(9, 5), dpi=100, facecolor=theme.SURFACE)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("figure_leave_event", lambda e: self._hide_hover())
        self.plotted = []  # [(PriceHistory, color)] currently on the axes
        self._style_axes()

    @property
    def widget(self):
        return self.canvas.get_tk_widget()

    def show_message(self, text):
        self.ax.clear()
        self._style_axes()
        self.plotted = []
        self.ax.set_title(text, color=theme.INK_SECONDARY, fontsize=11, loc="left")
        self.canvas.draw_idle()

    def plot(self, histories_with_colors, title):
        ax = self.ax
        ax.clear()
        self._style_axes()

        self.plotted = list(histories_with_colors)
        for history, color in self.plotted:
            ax.plot(history.close.index, history.close.values,
                    color=color, linewidth=2)
            # Direct label at the line's end instead of numbers on every point.
            ax.annotate(f" {history.ticker}  {history.last:,.2f}",
                        xy=(history.close.index[-1], history.last),
                        color=color, fontsize=9, fontweight="bold",
                        va="center", annotation_clip=False)

        if len(self.plotted) > 1:
            ax.legend([h.ticker for h, _ in self.plotted], loc="upper left",
                      frameon=False, fontsize=9,
                      labelcolor=theme.INK_SECONDARY)
        ax.set_title(title, color=theme.INK_PRIMARY, fontsize=12,
                     fontweight="bold", loc="left", pad=12)
        ax.set_ylabel("Price", color=theme.INK_MUTED, fontsize=9)

        locator = mdates.AutoDateLocator()
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        ax.margins(x=0.02)
        self.fig.subplots_adjust(left=0.07, right=0.90, top=0.90, bottom=0.10)

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

    # ---------- Hover ----------

    def _on_hover(self, event):
        if not self.plotted or event.inaxes != self.ax:
            self._hide_hover()
            return
        when = mdates.num2date(event.xdata)
        lines, xs, ys, colors = [], [], [], []
        for history, color in self.plotted:
            series = history.close
            idx = series.index.tz_localize(None) if series.index.tz else series.index
            pos = idx.get_indexer([when.replace(tzinfo=None)], method="nearest")[0]
            xs.append(mdates.date2num(series.index[pos]))
            y = float(series.iloc[pos])
            ys.append(y)
            colors.append(color)
            lines.append(f"{history.ticker}  {y:,.2f}")
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

    def _style_axes(self):
        ax = self.ax
        ax.set_facecolor(theme.SURFACE)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(theme.BASELINE)
            ax.spines[side].set_linewidth(0.8)
        ax.tick_params(colors=theme.INK_MUTED, labelsize=9, length=3)
        ax.grid(True, axis="y", color=theme.GRIDLINE, linewidth=0.7)
        ax.set_axisbelow(True)
