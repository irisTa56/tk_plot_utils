"""Submodule for making Plotly's trace instances."""

import numpy as np

from .plotly_html import  pltgo

def make_scatter(data):
  """Creates a list of ``plotly.graph_objs.Scatter`` instance(s),
  then return it.

  Parameters:

  data: dict or list/tuple of dict
    Scatter instance (trace) is created from this dictionary.
    If list/tuple of dictionaries are given, multiple instances
    will be created. Regardless of the number of created instances,
    a list of instance(s) is returned.

    For more details:

    >>> import tk_plot_utils as tk
    >>> help(tk.go.Scatter)

  """
  if isinstance(data, dict):
    data = [data]
  elif not isinstance(data, (list, tuple)):
    raise TypeError("Invalid type of data: {}".format(type(data)))

  return [pltgo.Scatter(d) for d in data]

def make_heatmap(data):
  """Creates a list of ``plotly.graph_objs.Heatmap`` instance(s),
  then return it.

  Parameters:

  data: dict or list/tuple of dict
    Heatmap instance (trace) is created from this dictionary.
    If list/tuple of dictionaries are given, multiple instances
    will be created. Regardless of the number of created instances,
    a list of instance(s) is returned.

    For more details:

    >>> import tk_plot_utils as tk
    >>> help(tk.go.Heatmap)

  """
  if isinstance(data, dict):
    data = [data]
  elif not isinstance(data, (list, tuple)):
    raise TypeError("Invalid type of data: {}".format(type(data)))

  for d in data:

    if "transpose" not in d:
      d["transpose"] = True

    nx, ny = np.array(d["z"]).shape

    if not d["transpose"]:
      nx, ny = ny, nx

    if "x0" in d or "y0" in d:
      if "x0" in d and "y0" in d:
        print("Values of 'x0' and 'y0' will be used for 'origin'")
        d["origin"] = (d["x0"], d["y0"])
      else:
        raise RuntimeError("Both 'x0' and 'y0' are required")

    if "origin" in d:

      if "dx" not in d or "dy" not in d:
        raise RuntimeError("Both 'dx' and 'dy' are required")

      if "x" in d:
        print("Value of 'x' will be overwritten")
      if "y" in d:
        print("Value of 'y' will be overwritten")

      dx, dy = d["dx"], d["dy"]

      d["x"] = d["origin"][0] + np.arange(nx+1)*dx
      d["y"] = d["origin"][1] + np.arange(ny+1)*dy

      del d["origin"]

    elif not ("x" in d and "y" in d):
      raise RuntimeError("Either 'origin' or 'x' and 'y' are required")

  return [pltgo.Heatmap(d) for d in data]