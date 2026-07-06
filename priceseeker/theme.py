"""Colors for charts and widgets (light surface).

Categorical series colors are assigned in fixed order — ticker N always
gets slot N for the lifetime of one chart, never cycled or reshuffled.
"""

SURFACE = "#fcfcfb"
PAGE = "#f9f9f7"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"

SERIES = ["#2a78d6", "#1baf7a", "#eda100", "#008300",
          "#4a3aa7", "#e34948", "#e87ba4", "#eb6834"]

# Indicator overlays. These only appear on single-ticker charts, where the
# price line is SERIES[0] blue, so clashes with later SERIES slots are moot.
IND_SMA = "#eda100"
IND_EMA = "#4a3aa7"
IND_BAND = "#7d9ec4"
IND_RSI = "#2a78d6"
IND_VOL = "#aebfd4"  # volume bars
