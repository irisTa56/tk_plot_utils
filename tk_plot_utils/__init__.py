from .plotly_utils import plt as pl
from .plotly_utils import pltgo as go
from .plotly_utils import ExtendedFigureWidget as plotly

init_plotly = pl.init_notebook_mode

__all__ = [
  "init_plotly",
  "pl",
  "go",
  "plotly",
]
