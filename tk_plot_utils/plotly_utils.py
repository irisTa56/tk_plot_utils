"""Submodule for a class inheriting ``plotly.graph_objs.FigureWidget``."""

import re
import copy as cp
import numpy as np
import itertools as it
import collections as co

from datetime import datetime

from plotly import tools

from .plotly_html import  plt, pltgo, override
from .utility_functions import merged_dict

#=======================================================================

class ExtendedFigureWidget(pltgo.FigureWidget):
  """Inheriting ``plotly.graph_objs.FigureWidget``.

  Original FigureWidget's functionalities *plus* the following features.

  * Show myself (using ``plotly.offline.iplot()``).
  * Make subplots (using ``plotly.tools.make_subplots()``).
  * Manage legend and titles.
  * Manage axis layout.

  .. note::
    Static Members:

    default_layout: dict
      ExtendedFigureWidget is initialized with this layout.

    unitalicized: list of str
      Strings in this list will not be italicized in a symbol of axis title.

  """

  default_layout = {
    "width": 450,
    "height": 450,
    "font": {
      "family": "Arial",
      "size": 18,
    },
    "title": {
      "font": {"size": 20},
      "xanchor": "center",
      "xref": "paper",
      "yanchor": "middle",
      "yref": "container",
    },
    "margin": {
      "b": 20,
      "l": 20,
      "r": 20,
      "t": 80
    }
  }

  unitalicized = ["(", ")", "sin", "cos", "tan", "exp", "log"]
  unitalicized += list(map(str, range(10)))

  def __init__(self, *args, **kwargs):
    """
    Parameters:

    args:
      Directly passed to ``super().__init__()``.

    kwargs:
      Directly passed to ``super().__init__()``.

    """
    super().__init__(*args, **kwargs)

    self._init_layout()
    self._init_axis()

    # required to delete dummy data used for showing mirror/minor axis
    self._dummy_uids = []

    # whether this instance has subplots or not
    self._has_subplots = False

    # required to align axis range in subplots
    self._range_alignment = {}

  def show(self, data=None, **kwargs):
    """Show a plot of data contained in this instance
    using ``plotly.offline.iplot()``.

    Parameters:

    data: list or tuple
      List or tuple of trace instances (scatter, heatmap, etc.)
      to be plotted. These instances are added to ``self.data``
      before calling ``plotly.offline.iplot()``.
      If None, there is no addition of data.

    kwargs:
      Passed to ``plotly.offline.iplot()``.

      For more details:

      >>> import tk_plot_utils as tk
      >>> help(tk.pl.iplot)

    """
    if isinstance(data, (tuple, list)):
      self._set_data(data)

    self._layout_all()

    auto_kwargs = {
      "show_link": False,
      "image": "svg",
      "image_width": self.layout.width,
      "image_height": self.layout.height,
      "filename": "plot-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
    }

    auto_kwargs.update(kwargs)

    dct = {
      a["name"]: i for i, a in enumerate(self.layout.annotations)
      if isinstance(a.name, str) and a.name.endswith("-title")
    } if "annotations" in self.layout else {}

    override(dct.get("x-title"), dct.get("y-title"))

    plt.iplot(self, **auto_kwargs)

    self._clear_dummy_traces()

  def subplots(
    self, trace_array, share="", align={},
    xspace_factor=1.0, yspace_factor=1.0, **kwargs):
    """Make subplots from an array of trace instances
    using ``plotly.tools.make_subplots()``.

    Parameters:

    trace_array: list
      Two-dimensional list containing trace instances.
      Shape and arrangement of this list must correspond to
      those of subplots.

    share: str
      Specify shared axis. If 'x', traces in the same column share
      one *x* axis. If 'y', traces in the same row share one *y* axis.
      If 'xy', both *x* and *y* axes are shared.

    align: dict
      Dictionary of which keys are 'row' and/or 'col'
      and values are 'each' and/or 'all'.

      Examples:

        * ``align={'col': 'each'}`` aligns initial ranges of *x* axes
          in each column.
        * ``align={'row': 'each'}`` aligns initial ranges of *y* axes
          in each row.
        * ``align={'col': 'all'}`` aligns initial range of all *x* axes.

    xspace_factor: float
      Factor multiplied to size of horizontal (in *x* direction) spacing
      between the subplots. Value greater than 1 leads to wider space,
      and less than 1 leads to narrower space.

    yspace_factor: float
      Factor multiplied to size of vertical (in *x* direction) spacing
      between the subplots. Value greater than 1 leads to wider space,
      and less than 1 leads to narrower space.

    kwargs:
      Passed to ``plotly.tools.make_subplots()``.

      For more details:

      >>> import tk_plot_utils as tk
      >>> help(tk.tools.make_subplots)

    """
    trace_list = self._make_subplots(
      trace_array, share, xspace_factor, yspace_factor, **kwargs)

    if align:
      self._subplots_range_alignment(align)

    self._set_data(trace_list)

    self._has_subplots = True

  def set_legend(
    self, position=None, padding=10, xpad=None, ypad=None, **kwargs):
    """Set layout of the legend.

    Calling this method with no parameter hides the legend.

    Parameters:

    position: str
      One of 'upper right', 'lower right', 'upper left', 'lower left',
      'custom' or 'default'.

    padding: number
      Distance (in pixel) between the legend and frame line of the plot
      (legend is inside the frame).

    xpad: number
      Horizontal distance (in pixel) between the legend and frame line
      of the plot (legend is inside the frame).
      If None, ``padding`` will be used.

    ypad: number
      Vertical distance (in pixel) between the legend and frame line
      of the plot (legend is inside the frame).
      If None, ``padding`` will be used.

    kwargs:
      Assigned to ``self.layout.legend``.
      If ``position`` is neither 'custom' nor 'default', values for 'x',
      'y', 'xanchor' and 'yanchor' will be updated.

    """
    self.layout.showlegend = False if position is None else True
    self.layout.legend = {} if position == "default" else kwargs

    if position is None or position == "default" or position == "custom":
      pass
    elif any(
      position == s
      for s in ["upper right", "lower right", "upper left", "lower left"]):

      # NOTE: The following two lines try to convert `padding` unit
      # to normalized coordinates. But, since actual domain size is
      # different from `self.layout.width* self.layout.height`,
      # this conversion is not precise.
      xpadding = (padding if xpad is None else xpad) / self.layout.width
      ypadding = (padding if ypad is None else ypad) / self.layout.height

      vertical, horizontal = position.split()

      x = 1-xpadding if horizontal == "right" else xpadding
      y = 1-ypadding if vertical == "upper" else ypadding
      xanchor =  "right" if horizontal == "right" else "left"
      yanchor = "top" if vertical == "upper" else "bottom"

      self.layout.legend.update({
        "x": x, "xanchor": xanchor,
        "y": y, "yanchor": yanchor,
      })
    else:
      raise ValueError("Unrecognized position: {}".format(position))

  def set_title(self, title, shift=0, font={}):
    """Set a title string.

    Parameters:

    title: str
      Title string.

    shift: number
      Shift (in pixel) from default *y* position.
      The default position is middle of the top margin area.

    font: dict
      Dictionary specifying a font setting.

    """
    h = self.layout.height
    t = self.layout.margin.t

    self.layout.title.update(text=title, y=(h-0.5*t+shift)/h)

    if font:
      self.layout.title.update(font=font)

  # Axis Management ----------------------------------------------------

  def set_axis_title(
    self, axis, name=None, symbol=None, unit=None, font={}):
    """Set a title string to the given axis.

    Axis title consists of three parts: *name*, *symbol* and *unit*.
    The entire title is something like "name, *symbol* [unit]".
    If all the three parts are not explicitly specified,
    title of the given axis is removed.

    Parameters:

    axis: str
      Name of axis which the title is set to.

    name: str
      Main part of axis title.

    symbol: str
      Symbol representing the title. This part is italicized.

    unit: str
      Unit of the axis. This is also an important part of axis title!

    font: dict
      Dictionary specifying a font setting.

    """
    if len(axis) == 2 and axis[1] == "1":
      axis = axis[0]

    if axis not in self._axes:
      self._create_axis(axis)

    if name is None and symbol is None and unit is None:
      if "text" in self._axes[axis].layout["title"]:
        del self._axes[axis].layout["title"]["text"]
    else:
      title = self._make_axis_title_string(name, symbol, unit)
      self._axes[axis].layout["title"]["text"] = title
      if font:
        self._axes[axis].layout["title"]["font"] = font

  def set_x_title(self, name=None, symbol=None, unit=None, font={}):
    """Set a title string to *x* axis.

    If this instance has subplots, this method sets a single title
    for *x* axis. The single title is at the center of dummy titles
    of *x* axes. In other words, horizontal position of the title is
    at the center of the plot area.
    If this instance has no subplots, this method calls
    ``self.set_axis_title()`` with the newest created *x* axis.

    .. note::
      Parameters have the same meanings
      as those of ``self.set_axis_title()``.

    """
    if self._has_subplots:
      for subplot in self._grid_ref[-1]:
        self.set_axis_title(subplot[0], "<span>\u0020</span>")  # dummy title
      self._set_single_x_title(
        self._make_axis_title_string(name, symbol, unit), font)
    else:
      xaxes = [k for k in self._axes.keys() if k.startswith("x")]
      if len(xaxes) > 1:
        print("Warning: Set title for 1 of {} x axes".format(len(xaxes)))
      self.set_axis_title(xaxes[0], name, symbol, unit, font)

  def set_y_title(self, name=None, symbol=None, unit=None, font={}):
    """Set a title string to *y* axis.

    If this instance has subplots, this method sets a single title
    for *y* axis. The single title is at the middle of dummy titles
    of *y* axes. In other words, vertical position of the title is
    at the middle of the plot area.
    If this instance has no subplots, this method calls
    ``self.set_axis_title()`` with the newest created *y* axis.

    .. note::
      Parameters have the same meanings
      as those of ``self.set_axis_title()``.

    """
    if self._has_subplots:
      for subplot in [row[0] for row in self._grid_ref]:
        self.set_axis_title(subplot[1], "<span>\u0020</span>")  # dummy title
      self._set_single_y_title(
        self._make_axis_title_string(name, symbol, unit), font)
    else:
      yaxes = [k for k in self._axes.keys() if k.startswith("y")]
      if len(yaxes) > 1:
        print("Warning: Set title for only 1 of {} y axes".format(len(yaxes)))
      self.set_axis_title(yaxes[0], name, symbol, unit, font)

  def clear_axis_title(self, direc="xy"):
    """Clear axis title.

    Parameters:

    direc: str
      If ``direc`` contains 'x' and/or 'y',
      all axis titles of the direction(s) are removed.

    """
    for d in direc:

      for axis in (k for k in self._axes.keys() if k.startswith(d)):
        self.set_axis_title(axis)

      if "annotations" in self.layout:
        self.layout.annotations = tuple(
          a for a in self.layout.annotations
          if "name" not in a or a.name != d+"-title")

  def set_axis_range(self, axis, minimum=None, maximum=None):
    """Set a range to the given axis.

    Parameters:

    axis: str (can be a regular expression)
      Name of axis which the range is set to.
      You can specify multiple axes using a regular expression.

    minimum: number
      Minimum of the range.

    maximum: number
      Maximum of the range.

    """
    if axis in self._axes and (minimum is None and maximum is None):
      self.delete_axis_layout(axis, "range")
    elif minimum is not None and maximum is not None:
      self.set_axis_layout(axis, "range", [minimum, maximum])

  def set_x_range(self, minimum=None, maximum=None):
    """Set a range to all the *x* axes.

    Parameters:

    minimum: number
      Minimum of the range.

    maximum: number
      Maximum of the range.

    """
    self.set_axis_range("x\d*", minimum, maximum)

  def set_y_range(self, minimum=None, maximum=None):
    """Set a range to all the *y* axes.

    Parameters:

    minimum: number
      Minimum of the range.

    maximum: number
      Maximum of the range.

    """
    self.set_axis_range("y\d*", minimum, maximum)

  def set_axis_ticks(self, axis, interval, num_minor=5, logtick=None):
    """Set ticks of the given axis.

    Parameters:

    axis: str (can be a regular expression)
      Name of axis which the range is set to.
      You can specify multiple axes using a regular expression.

    interval: number
      Distance between two consecutive major ticks.

    num_minor: int
      Number of minor ticks per major tick.

    logtick: str
      Special values for minor ticks of logarithmic axis;
      'L<f>', where ``f`` is a positive number, gives ticks linearly
      spaced in value (but not position). For example ``tick0`` = 0.1,
      ``dtick`` = 'L0.5' will put ticks at 0.1, 0.6, 1.1, 1.6 etc.
      To show powers of 10 plus small digits between,
      use 'D1' (all digits) or 'D2' (only 2 and 5).
      ``tick0`` is ignored for 'D1' and 'D2'.

    """
    self.delete_axis_layout(axis, "tickmode")
    self.delete_axis_layout(axis, "nticks")
    self.set_axis_layout(
      axis, "dtick", interval,
      minor_val=interval/num_minor if logtick is None else logtick)

  def set_x_ticks(self, interval, num_minor=5):
    """Set ticks of all the *x* axes.

    Parameters:

    interval: number
      Distance between two consecutive major ticks.

    num_minor: int
      Number of minor ticks per major tick.

    """
    self.set_axis_ticks("x\d*", interval, num_minor)

  def set_y_ticks(self, interval, num_minor=5):
    """Set ticks of all the *y* axes.

    Parameters:

    interval: number
      Distance between two consecutive major ticks.

    num_minor: int
      Number of minor ticks per major tick.

    """
    self.set_axis_ticks("y\d*", interval, num_minor)

  def set_axis_layout(
    self, axis, key, value, **kwargs):
    """Set a layout setting for the given axis.

    Parameters:

    axis: str (can be a regular expression)
      Name of axis which the range is set to.
      You can specify multiple axes using a regular expression.

    key: str
      Key for the layout setting.

    value: any
      Value for the layout setting.

      For more details:

      >>> import tk_plot_utils as tk
      >>> help(tk.go.layout.XAxis)  # or help(tk.go.layout.YAxis)

    kwargs:
      * ``mirror_val`` : replace ``value`` for sub-axis
        used for drawing mirrored ticks.
      * ``minor_val`` : replace ``value`` for sub-axis
        used for drawing minor ticks.

    """
    if re.match("[xy]\d*$", axis):
      if len(axis) == 2 and axis[1] == "1":  # x1/y1 should be x/y
        axis = axis[0]
      if axis not in self._axes:
        self._create_axis(axis)
        print("New axis has been created: {}".format(axis))
      self._axes[axis].set_layout(key, value, **kwargs)
    else:
      for k, v in self._axes.items():
        if re.match(axis, k) or k in "xy" and re.match(axis, "{}1".format(k)):
          v.set_layout(key, value, **kwargs)

  def delete_axis_layout(self, axis, key):
    """Delete a layout setting of the given axis.

    Parameters:

    axis: str (can be a regular expression)
      Name of axis which the range is set to.
      You can specify multiple axes using a regular expression.

    key: str
      Key for the layout setting.

    """
    if re.match("[xy]\d*$", axis):
      if len(axis) == 2 and axis[1] == "1":  # x1/y1 should be x/y
        axis = axis[0]
      if axis not in self._axes:
        self._create_axis(axis)
        print("New axis has been created: {}".format(axis))
      self._axes[axis].delete_layout(key)
    else:
      for k, v in self._axes.items():
        if re.match(axis, k) or k in "xy" and re.match(axis, "{}1".format(k)):
          v.delete_layout(key)

  # Private Methods ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  # Initialization/Creation --------------------------------------------

  def _init_layout(self):
    """Initialize ``self._layout``
    by merging *static* ``default_layout`` with *super* ``self._layout``."""
    self._layout = merged_dict(type(self).default_layout, self._layout)

  def _init_axis(self):
    """Initialize ``self._axes``,
    which keeps MirroredAxisWithMinorTick instances."""
    self._axes = {}

    for k in self._layout.keys():
      if re.match("[xy]axis\d*$", k):
        self._create_axis(k.replace("axis", ""))

    if "xaxis" not in self._layout:
      self._create_axis("x")

    if "yaxis" not in self._layout:
      self._create_axis("y")

  # Layout -------------------------------------------------------------

  def _layout_all(self):
    """Arrange all traces."""
    dct = co.defaultdict(list)

    for d in self.data:
      if isinstance(d, pltgo.Scatter):
        dct["scatter"].append(d)
      elif isinstance(d, pltgo.Heatmap):
        dct["heatmap"].append(d)
      else:
        raise TypeError("Non supported data type: {}".format(type(d)))

    if "scatter" in dct:
      self._layout_scatter(dct["scatter"])
    if "heatmap" in dct:
      self._layout_heatmap(dct["heatmap"])

  def _layout_scatter(self, scatters):
    """Arrange *Scatter* traces."""
    # create all axis & categorize scatters by their axis

    dct = co.defaultdict(list)

    for scatter in scatters:

      axis_pair = (
        scatter.xaxis if scatter.xaxis else "x",
        scatter.yaxis if scatter.yaxis else "y")

      for axis in axis_pair:
        if axis not in self._axes:
          self._create_axis(axis)

      dct[axis_pair].append(scatter)

    # setting for each axis

    skip_range_setting = {
      k: v.in_layout("range") for k, v in self._axes.items()
    }

    skip_ticks_setting = {
      k: v.in_layout("dtick") for k, v in self._axes.items()
    }

    for axis_pair, scatters in dct.items():

      for axis in axis_pair:

        if not skip_range_setting[axis]:
          if self._axes[axis].layout.get("type") == "log":
            minimum = np.log10(min(min(s[axis[0]]) for s in scatters))
            maximum = np.log10(max(max(s[axis[0]]) for s in scatters))
            padding = 0.05 * (maximum - minimum)
          else:
            minimum = min(min(s[axis[0]]) for s in scatters)
            maximum = max(max(s[axis[0]]) for s in scatters)
            # set padding in y direction only
            padding = 0 if axis[0] == "x" else 0.05 * (maximum - minimum)
          self._extend_axis_range(axis, minimum-padding, maximum+padding)

        if not skip_ticks_setting[axis]:
          if self._axes[axis].layout.get("type") == "log":
            self.set_axis_ticks(
              axis, *self._auto_axis_ticks(
                self._axes[axis].layout["range"], log=True))
          else:
            self.set_axis_layout(axis, "tickmode", "auto")
            self.set_axis_layout(axis, "nticks", 6, minor_val=34)

      self._add_dummy_traces(axis_pair, self.add_scatter)

    if self._range_alignment:
      self._align_subplots_range()

  def _layout_heatmap(self, heatmaps, auto_size=True):
    """Arrange *Heatmap* traces."""
    # create all axis & categorize heatmaps by their axis

    dct = {}

    for heatmap in heatmaps:

      axis_pair = (
        heatmap.xaxis if heatmap.xaxis else "x",
        heatmap.yaxis if heatmap.yaxis else "y")

      for axis in axis_pair:
        if axis in dct:
          raise RuntimeError(
            "{} is already used by {}".format(axis, dct[axis]))
        if axis not in self._axes:
          self._create_axis(axis)

      dct[axis_pair] = heatmap

    # setting for each axis

    skip_range_setting = {
      k: v.in_layout("range") for k, v in self._axes.items()
    }

    skip_ticks_setting = {
      k: v.in_layout("dtick") for k, v in self._axes.items()
    }

    for axis_pair, heatmap in dct.items():

      nx, ny = np.array(heatmap.z).shape

      if not heatmap.transpose:
        nx, ny = ny, nx

      for axis, n, v in zip(axis_pair, (nx, ny), (heatmap.x, heatmap.y)):

        if not skip_range_setting[axis]:
          minimum = v[0] if len(v) == n+1 else v[0] - 0.5*(v[1]-v[0])
          maximum = v[-1] if len(v) == n+1 else v[-1] + 0.5*(v[-1]-v[-2])
          self._extend_axis_range(axis, minimum, maximum)

        if not skip_ticks_setting[axis]:
          self.set_axis_layout(axis, "tickmode", "auto")
          self.set_axis_layout(axis, "nticks", 6, minor_val=34)

        self._axes[axis].set_layout("ticks", "outside")
        self._axes[axis].set_layout("constrain", "domain")

      self._axes[axis_pair[1]].layout["scaleanchor"] = axis_pair[0]

      self._add_dummy_traces(axis_pair, self.add_heatmap)

    if self._range_alignment:
      self._align_subplots_range()

  # Dummy Traces -------------------------------------------------------

  def _add_dummy_traces(self, axis_pair, callback):
    """Add dummy traces required to show mirror and minor ticks."""
    namepair_list = [
      *it.product(*(self._axes[axis].mirrors for axis in axis_pair)),
      *it.product(*(self._axes[axis].minors for axis in axis_pair))]

    for namepair in namepair_list:
      dummy = callback(**{
        "visible": False,
        **{"{}axis".format(name[0]): name for name in namepair}
      })
      self._dummy_uids.append(dummy["uid"])

  def _clear_dummy_traces(self):
    """Delete all dummy traces of which 'uid' is in ``self._dummy_uids``."""
    prev_len = len(self.data)

    self.data = tuple(
      d for d in self.data if d.uid not in self._dummy_uids)

    if prev_len - len(self.data) == len(self._dummy_uids):
      self._dummy_uids.clear()
    else:
      raise RuntimeError("Dummy trace might be deleted accidentally")

  # Subplots -----------------------------------------------------------

  def _make_subplots(
    self, trace_array, share, xspace_factor=1.0, yspace_factor=1.0, **kwargs):
    """Make subplots using ``plotly.tools.make_subplots()``."""
    self._clear_axes()

    kwargs["shared_xaxes"] = "x" in share
    kwargs["shared_yaxes"] = "y" in share

    if "specs" in kwargs:
      if not self._compare_grid(kwargs["specs"], trace_array):
        raise RuntimeError("Shape of specs differs from that of trace array")
    else:
      kwargs["specs"] = [
        [{} if cell else None for cell in row] for row in trace_array]

    n_row, n_col = self._get_grid_shape(kwargs["specs"])

    kwargs["horizontal_spacing"] = xspace_factor * (
      0.1 if kwargs["shared_yaxes"] else 0.2) / n_col
    kwargs["vertical_spacing"] = yspace_factor * (
      0.1 if kwargs["shared_xaxes"] else 0.3) / n_row

    fig = tools.make_subplots(rows=n_row, cols=n_col, **kwargs)

    # store axis layout of created Figure instance
    axis_layouts = {
      k.replace("axis", ""): v
      for k, v in fig._layout.items() if re.match("[xy]axis\d*$", k)
    }

    # set subplot titles
    if "annotations" in fig.layout:
      for annotation in fig.layout.annotations:
        annotation["font"] = self.layout.title.font.to_plotly_json()
      if "annotations" in self.layout:
        self.layout.annotations += fig.layout.annotations
      else:
        self.layout.annotations = fig.layout.annotations

    # convert x1/y1 to x/y
    self._grid_ref = [
      [
        tuple(a[0] if a[1:] == "1" else a for a in cell)
        if cell else None for cell in row
      ]
      for row in fig._grid_ref
    ]

    flatten_array = []

    # loop from bottom
    for row1, row2 in zip(trace_array[::-1], self._grid_ref[::-1]):
      flatten_row = []
      for cell, axis_pair in zip(row1, row2):
        if cell is None: continue

        for trace in cell if isinstance(cell, (list, tuple)) else [cell]:
          trace.xaxis, trace.yaxis = axis_pair
          flatten_row.append(trace)

        for axis, opposite in [axis_pair, axis_pair[::-1]]:
          tmp_layout = cp.deepcopy(axis_layouts[axis])
          # NOTE: Official tools.make_subplots() uses 'free' as anchor.
          # Will something wrong occur by assigning opposite axis as anchor?
          tmp_layout["anchor"] = opposite
          if axis not in self._axes:
            self._create_axis(axis, **tmp_layout)
          else:
            self._axes[axis].append_mirror_axis(**tmp_layout)
            self._axes[axis].append_minor_axis(**tmp_layout)

      flatten_array = flatten_row + flatten_array

    return flatten_array

  def _compare_grid(self, grid1, grid2):
    """Whether shapes of two grids are equivalent or not."""
    for row1, row2 in zip(grid1, grid2):
      for cell1, cell2 in zip(row1, row2):
        if (cell1 is None) != (cell2 is None):
          return False
    return True

  def _get_grid_shape(self, grid):
    """Return the number of rows and columns of the given grid."""
    n_row = len(grid)
    n_col = len(grid[0])
    if not all(len(row) == n_col for row in grid):
      raise RuntimeError("Invalid shape of subplot grid")

    return n_row, n_col

  def _subplots_range_alignment(self, align):
    """Setting for range alignment of subplots."""
    self._range_alignment.clear()

    if "x" in align:
      master_axes = [pair[0] for pair in self._grid_ref[0]]

      if align["x"] == "each":
        for row in self._grid_ref:
          for icol, pair in enumerate(row):
            self._append_range_alignment(master_axes[icol], pair[0])

      elif align["x"] == "all":
        for row in self._grid_ref:
          for pair in row:
            self._append_range_alignment(master_axes[0], pair[0])

      else:
        raise RuntimeError(
          "Invalid align scheme for x: {}".format(align["x"]))

    if "y" in align:
      master_axes = [pair[1] for pair in [row[0] for row in self._grid_ref]]

      if align["y"] == "each":
        for irow, row in enumerate(self._grid_ref):
          for pair in row:
            self._append_range_alignment(master_axes[irow], pair[1])

      elif align["y"] == "all":
        for row in self._grid_ref:
          for pair in row:
            self._append_range_alignment(master_axes[0], pair[1])

      else:
        raise RuntimeError(
          "Invalid align scheme for y: {}".format(align["y"]))

    self._show_range_alignment()

  def _align_subplots_range(self):
    """Align axis range of subplots."""
    for k, v in self._range_alignment.items():

      axis_types = set(self._axes[axis].layout.get("type") for axis in v)
      if len(axis_types) == 1:
        axis_type = list(axis_types)[0]
      else:
        raise RuntimeError("Aligned axes must have the same axis type")

      minimum = min(self._axes[axis].layout["range"][0] for axis in v)
      maximum = max(self._axes[axis].layout["range"][1] for axis in v)
      self.set_axis_range(k, minimum, maximum)

      if axis_type == "log":
        self.set_axis_ticks(
          k, *self._auto_axis_ticks(
            self._axes[k].layout["range"], log=True))

  def _append_range_alignment(self, master, axis):
    """Append new axis to ``self._range_alignment``."""
    if master in self._range_alignment:
      self._range_alignment[axis] = self._range_alignment[master]
      self._range_alignment[axis].append(axis)
    elif master == axis:
      self._range_alignment[axis] = [axis]
    else:
      raise RuntimeError("Invalid range alignment")

  def _show_range_alignment(self):
    """Show ``self._range_alignment``."""
    if self._range_alignment:
      print("reference for range alignment:")

    for k, v in self._range_alignment.items():
      print("{:3s}: min/max of {}".format(k,v))

  def _show_subplot_grid(self, subplots):
    """Show axis pair corresponding to each subplot grid."""
    print("subplot grid:")

    maxlen = max(len(s) for s in sum(subplots, []))

    for row in subplots:
      print("| {} |".format(" | ".join(
        format(s, "^{}s".format(maxlen)) for s in row)))

  # Axis Management ----------------------------------------------------

  def _create_axis(self, axis, **kwargs):
    """Create an instance of MirroredAxisWithMinorTick."""
    self._axes[axis] = MirroredAxisWithMinorTick(axis, self._layout, **kwargs)

  def _clear_axes(self):
    """Remove all axis layouts."""
    self._axes.clear()
    axis_layout_keys = [
      k for k in self._layout.keys() if re.match("[xy]axis\d*$", k)]
    for k in axis_layout_keys:
      del self._layout[k]

  def _make_axis_title_string(self, name=None, symbol=None, unit=None):
    """Make a string for axis title."""
    title = str(name)

    if symbol is not None:

      for s in type(self).unitalicized:
        symbol = symbol.replace(s, "</i>{}<i>".format(s))

      title += ", <i>{}</i>".format(symbol)

    if unit is not None:
      title += " [{}]".format(unit)

    return title

  def _extend_axis_range(self, axis, minimum, maximum):
    """Extend range of the given axis.

    If the range has not been set yet,
    ``minimum`` and ``maximum`` will be set as it is.
    """
    if self._axes[axis].in_layout("range"):
      self.set_axis_range(
        axis,
        min(minimum, self._axes[axis].layout["range"][0]),
        max(maximum, self._axes[axis].layout["range"][1]))
    else:
      self.set_axis_range(axis, minimum, maximum)

  def _auto_axis_ticks(self, axis_range, log=False):
    """Automatically determine ``interval`` and ``num_minor``,
    which are parameters of ``self.set_axis_ticks()``.
    """
    if log:

      if axis_range[1]-axis_range[0] > 2:  # NOTE: 2 is the best?
        return 1, None, "D1"
      else:
        tmpd = (
          np.power(10, axis_range[1])
          - np.power(10, axis_range[0])) / 3  # at least 3 tick labels
        order = int(np.floor(np.log10(tmpd)))
        scaled = tmpd/(10**order)

        d_linear = (
          5 if 5 < scaled else 2 if 2 < scaled else 1) * 10**order

        return "L{}".format(d_linear), None, "L{}".format(d_linear/5)

    else:

      tmpd = (axis_range[1]-axis_range[0]) / 3  # at least 3 tick labels
      order = int(np.floor(np.log10(tmpd)))
      scaled = tmpd/(10**order)

      if 5 < scaled:
        return 5*10**order, 5
      elif 2 < scaled:
        return 2*10**order, 4
      else:
        return 10**order, 5

  def _set_single_x_title(self, title, font={}):
    """Add a single title of *x* axis to ``self.layout.annotations``."""
    title_layout = {
      "font": font if font else self.layout.title.font.to_plotly_json(),
      "name": "x-title",
      "showarrow": False,
      "text": title,
      "x": 0.5,
      "xanchor": "center",
      "xref": "paper",
      "y": 0.0,
      "yanchor": "bottom",
      "yref": "paper",
    }

    if "annotations" in self.layout:

      found = False

      for annotation in self.layout.annotations:
        if "name" in annotation and annotation.name == "x-title":
          found = True
          annotation.text = title
          if font:
            annotation.font = font

      if not found:
        self.layout.annotations += (title_layout,)

    else:
      self.layout.annotations = (title_layout,)

  def _set_single_y_title(self, title, font={}):
    """Add a single title of *y* axis to ``self.layout.annotations``."""
    title_layout = {
      "font": font if font else self.layout.title.font.to_plotly_json(),
      "name": "y-title",
      "showarrow": False,
      "text": title,
      "textangle": -90,
      "x": 0.0,
      "xanchor": "left",
      "xref": "paper",
      "y": 0.5,
      "yanchor": "middle",
      "yref": "paper",
    }

    if "annotations" in self.layout:

      found = False

      for annotation in self.layout.annotations:
        if "name" in annotation and annotation.name == "y-title":
          found = True
          annotation.text = title
          if font:
            annotation.font = font

      if not found:
        self.layout.annotations += (title_layout,)

    else:
      self.layout.annotations = (title_layout,)

  # Miscellaneous ------------------------------------------------------

  def _set_data(self, data):
    """Set the given data to ``self.data`` after clearing previous data."""
    self.data = tuple()
    self.add_traces(data)

#=======================================================================

class MirroredAxisWithMinorTick:

  common_default_layout = {
    "automargin": True,
    "zeroline": False,
    "showgrid": False,
    "ticks": "inside",
  }

  # NOTE: `mirror="ticks"` cannot be used,
  # because mirroring ticks breaks auto margin (for labeled axis).
  main_default_layout = {
    **cp.deepcopy(common_default_layout),
    "title": {
      "font": {"size": 20}
    },
    "showline": False,
    "showticklabels": True,
    "ticklen": 5,
    "tickfont": {"size": 18},
    "hoverformat": ".f",
  }

  mirror_default_layout = {
    **cp.deepcopy(common_default_layout),
    "showline": False,
    "showticklabels": False,
    "ticklen": 5,
  }

  minor_default_layout = {
    **cp.deepcopy(common_default_layout),
    "showline": True,  # only one axis may show line
    "showticklabels": False,
    "ticklen": 3,
    "mirror": "ticks",
  }

  opposite = {"x": "y", "y": "x"}
  mirror_side = {"x": "top", "y": "right"}

  def __init__(self, axis, parent_layout, **kwargs):
    self.name = axis
    self.parent_layout = parent_layout

    self.direc = axis[0]
    self.index = int(axis[1:]) if 1 < len(axis) else 1

    layout_key = "{}axis{}".format(
      self.direc, self.index if 1 < self.index else "")

    # NOTE: `self.layout` of this class is NOT an instance of
    # `plotly.graph_objs.Layout`, but just a Python dictionary.
    self.layout = self.parent_layout[layout_key] = merged_dict(
      type(self).main_default_layout,
      self.parent_layout.get(layout_key, {}))

    # ensure confort space between tick labels and axis line
    if self.direc == "y":
      self.layout["tickprefix"] = "\u2004"
      self.layout["ticksuffix"] = "\u2009"

    if "anchor" not in kwargs:
      kwargs["anchor"] = type(self).opposite[self.direc] + self.name[1:]

    self.layout.update(**kwargs)

    self.mirrors = []
    self.minors = []
    self._mirror_layouts = []
    self._minor_layouts = []

    self.append_mirror_axis(**kwargs)
    self.append_minor_axis(**kwargs)

  def delete_layout(self, key):
    """Delete a layout setting specified by *key*."""
    if key in self.layout:
      del self.layout[key]
    for mirror_layout in self._mirror_layouts:
      if key in mirror_layout:
        del mirror_layout[key]
    for minor_layout in self._minor_layouts:
      if key in minor_layout:
        del minor_layout[key]

  def set_layout(self, key, val, mirror_val=None, minor_val=None):
    """Set a layout setting specified by *key*."""
    if mirror_val is None:
      mirror_val = val
    if minor_val is None:
      minor_val = val

    # NOTE: Setting 'power' for 'exponentformat' magnifies font by 1.25 times,
    # see https://github.com/plotly/plotly.js/blob/4160081dd8b5136ba781039bd2b81588b2b36b4f/src/plots/cartesian/axes.js#L1111.
    # Setting 'tickfont' restores the original font size.
    if key == "exponentformat" and val == "power":
      self.layout["tickfont"]["size"] /= 1.25
    elif key == "tickformat" and self.layout.get("exponentformat") == "power":
      self.layout["tickfont"]["size"] *= 1.25

    self.layout[key] = val
    for mirror_layout in self._mirror_layouts:
      mirror_layout[key] = mirror_val
    for minor_layout in self._minor_layouts:
      minor_layout[key] = minor_val

  def in_layout(self, key):
    """Whether a layout setting specified by *key* exists ot not."""
    return all(
      key in layout for layout in [
        self.layout, *self._mirror_layouts, *self._minor_layouts])

  def append_mirror_axis(self, **kwargs):
    """Append an axis used for drawing mirrored (major) ticks."""
    mirror_index = 100 * (2*len(self._mirror_layouts)+1) + self.index

    mirror_layout_key = "{}axis{}".format(self.direc, mirror_index)

    mirror_layout = self.parent_layout[mirror_layout_key] = merged_dict(
      type(self).mirror_default_layout,
      self.parent_layout.get(mirror_layout_key, {}))

    mirror_layout["overlaying"] = self.name
    mirror_layout["scaleanchor"] = self.name

    if self.direc == "x":
      mirror_layout["side"] = type(self).mirror_side[self.direc]
      if self._mirror_layouts:
        del self._mirror_layouts[-1]["side"]
        self._mirror_layouts[-1]["mirror"] = "ticks"
    elif self.direc == "y":
      if self._mirror_layouts:
        mirror_layout["mirror"] = "ticks"
      else:
        mirror_layout["side"] = type(self).mirror_side[self.direc]

    mirror_layout.update(**kwargs)

    self.mirrors.append("{}{}".format(self.direc, mirror_index))
    self._mirror_layouts.append(mirror_layout)

  def append_minor_axis(self, **kwargs):
    """Append an axis used for drawing minor ticks."""
    minor_index = 100 * (2*len(self._minor_layouts)+2) + self.index

    minor_layout_key = "{}axis{}".format(self.direc, minor_index)

    minor_layout = self.parent_layout[minor_layout_key] = merged_dict(
      type(self).minor_default_layout,
      self.parent_layout.get(minor_layout_key, {}))

    minor_layout["overlaying"] = self.name
    minor_layout["scaleanchor"] = self.name

    minor_layout.update(**kwargs)

    self.minors.append("{}{}".format(self.direc, minor_index))
    self._minor_layouts.append(minor_layout)
