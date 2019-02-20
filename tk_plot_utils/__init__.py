"""An interface to Plotly"""

from ._version import __version__

from .plotly_html import init_plotly
from .plotly_traces import make_scatter, make_heatmap
from .plotly_utils import tools
from .plotly_utils import plt as pl
from .plotly_utils import pltgo as go
from .plotly_utils import ExtendedFigureWidget as plotly

__all__ = [
  "__version__",
  "pl",
  "go",
  "plotly",
  "make_scatter",
  "make_heatmap",
  "init_plotly",
  "tools",
]
