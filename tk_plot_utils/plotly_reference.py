"""Submodule containing functions to show Plotly's style reference."""

import IPython.display as ipd

from plotly.validators.scatter.marker._symbol import SymbolValidator
from plotly.validators.scatter.line._dash import DashValidator

html_template = """\
<ul>
  {}
</ul>
"""

item_template = """\
  <li><text class="btn btn-clipboard" data-clipboard-text="{0}">{0}</text></li>
"""

def ref_scatter_marker_symbol(start="", end=""):
  """Show a list of strings valid for values of ``Scatter.marker.symbol``.

  Strings can be copied to clipboard by clicking.

  Parameters:

  start: str
    Show strings only starting by this string .

  end: str
    Show strings only ending by this string.

  """
  ipd.display(ipd.HTML(html_template.format(
    "".join(
      item_template.format(s)
      for s in SymbolValidator().values
      if isinstance(s, str) and s.startswith(start) and s.endswith(end)))))

def ref_scatter_line_dash():
  """Show a list of strings valid for values of ``Scatter.line.dash``.

  Strings can be copied to clipboard by clicking.

  """
  ipd.display(ipd.HTML(html_template.format(
    "".join(
      item_template.format(s)
      for s in DashValidator().values if isinstance(s, str)))))