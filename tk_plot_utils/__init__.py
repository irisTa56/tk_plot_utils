from .plotly_html import init_plotly
from .plotly_utils import plt as pl
from .plotly_utils import pltgo as go
from .plotly_utils import ExtendedFigureWidget as plotly
from .plotly_utils import make_scatter, make_heatmap

__all__ = [
  "pl",
  "go",
  "plotly",
  "make_scatter",
  "make_heatmap",
  "init_plotly",
]
