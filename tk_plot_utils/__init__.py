from .plotly_utils import plt as pl
from .plotly_utils import pltgo as go
from .plotly_utils import ExtendedFigureWidget as plotly
from .plotly_utils import make_subplots, make_scatter, make_heatmap

init_plotly = pl.init_notebook_mode

__all__ = [
  "pl",
  "go",
  "plotly",
  "make_subplots",
  "make_scatter",
  "make_heatmap",
  "init_plotly",
]
