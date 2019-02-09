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

def make_scatter(data, **kwargs):
  """
  Function to create a list of `plotly.graph_objs.Scatter` instance(s)
  from `dict` (`list`/`tuple` of `dict`).
  """
  if isinstance(data, dict):
    data = [data]
  elif not isinstance(data, (list, tuple)):
    raise TypeError("Invalid type of data: {}".format(type(data)))

  return [pltgo.Scatter(d) for d in data]

def make_heatmap(data, **kwargs):
  """
  Function to create a list of `plotly.graph_objs.Heatmap` instance(s)
  from `dict` (`list`/`tuple` of `dict`).
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

#=======================================================================

class ExtendedFigureWidget(pltgo.FigureWidget):
  """
  Class wrapping `plotly.graph_objs.FigureWidget`.
  """

  default_layout = {
    "width": 450,
    "height": 450,
    "font": {
      "family": "Arial",
      "size": 18,
    },
    "titlefont": {
      "family": "Arial",
      "size": 20,
    },
    "margin": {
      "b": 0,
      "l": 0,
      "r": 10,
    }
  }

  unitalicized = ["(", ")", "sin", "cos", "tan", "exp", "log"]

  def __init__(self, *args, **kwargs):
    """
    Initializer of ExtendedFigureWidget class.
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
    """
    Method to show a plot of data contained in this instance.
    """
    if data is not None:
      self._set_data(data)

    self._layout_all(**kwargs)

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

    override(
      dct["x-title"] if "x-title" in dct else None,
      dct["y-title"] if "y-title" in dct else None)

    plt.iplot(self, **auto_kwargs)

    self._clear_dummy_traces()

  def subplots(
    self, trace_array, share="", align={}, **kwargs):
    """
    Method to make subplots from an array of trace instances.
    - `align` is a dictionary of which keys are 'row' or 'col'
      and values are 'each' or 'all'.
      - `align={'row': 'each'}` leads to that initial range of 'y*'
      ('*' is a wild card) axes in each row will be aligned.
      - `align={'col': 'all'}` leads to that initial range of all 'x*'
      axes will be aligned.
    """
    trace_list = self._make_subplots(trace_array, share, **kwargs)

    if align:
      self._subplots_range_alignment(align)

    self._set_data(trace_list)

    self._has_subplots = True

  def set_legend(
    self, position=None, padding=10, xpad=None, ypad=None, **kwargs):
    """
    Method to set layout of the legend. Calling this method with no
    parameter hides the legend.
    - `position` should be one of "upper right", "lower right",
      "upper left", "lower left" and "default".
    - `padding` is distance (in px) between the legend and frame line
      of the plot (legend is inside the frame).
    - `**kwargs` will be added to `plotly.graph_objs.Layout.legend`.
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
      xanchor =  "right" if horizontal == "right" else "left"
      y = 1-ypadding if vertical == "upper" else ypadding
      yanchor = "top" if vertical == "upper" else "bottom"

      self.layout.legend.update({
        "x": x, "xanchor": xanchor,
        "y": y, "yanchor": yanchor,
      })
    else:
      raise ValueError("Unrecognized position: {}".format(position))

  def set_title(self, title, space=30):
    """
    Method to set a title string using `self.layout.annotations`.
    - `space` is distance in pixel between bottom of the title and
      top of the main plot area.
    """
    title_layout = {
      "font": self._layout["titlefont"],
      "name": "title",
      "showarrow": False,
      "text": title,
      "x": 0.5,
      "xanchor": "center",
      "xref": "paper",
      "y": 1.0,
      "yanchor": "bottom",
      "yref": "paper",
      "yshift": space,
    }

    if "annotations" in self.layout:

      found = False

      for annotation in self.layout.annotations:
        if "name" in annotation and annotation.name == "title":
          found = True
          annotation.text = title
          annotation.yshift = space

      if not found:
        self.layout.annotations += (title_layout,)

    else:
      self.layout.annotations = (title_layout,)

  # Axis Management ----------------------------------------------------

  def set_axis_title(
    self, axis, name=None, char=None, unit=None):
    """
    Method to set a title string to the given axis.
    The string is something like `"{name}, <i>{char}</i> [{unit}]"`,
    if `char` and `unit` are provided.
    """
    if len(axis) == 2 and axis[1] == "1":
      axis = axis[0]

    if axis not in self._axes:
      self._create_axis(axis)

    if name is None and char is None and unit is None:
      self._axes[axis].delete_layout("title")
    else:
      title = self._make_axis_title_string(name, char, unit)
      self._axes[axis].layout["title"] = title

  def set_x_title(self, name=None, char=None, unit=None):
    """
    Method wrapping `self.set_axis_title()`.
    """
    if self._has_subplots:
      for subplot in self._grid_ref[-1]:
        self.set_axis_title(subplot[0], "<span>\u0020</span>")
      self._set_global_x_title(
        self._make_axis_title_string(name, char, unit))
    else:
      xaxes = [k for k in self._axes.keys() if k.startswith("x")]
      if len(xaxes) != 1:
        print("Warning: Set title for 1/{} x axis".format(len(xaxes)))
      self.set_axis_title(xaxes[0], name, char, unit)

  def set_y_title(self, name=None, char=None, unit=None):
    """
    Method wrapping `self.set_axis_title()`.
    """
    if self._has_subplots:
      for subplot in [row[0] for row in self._grid_ref]:
        self.set_axis_title(subplot[1], "<span>\u0020</span>")
      self._set_global_y_title(
        self._make_axis_title_string(name, char, unit))
    else:
      yaxes = [k for k in self._axes.keys() if k.startswith("y")]
      if len(yaxes) != 1:
        print("Warning: Set title for only 1/{} y axis".format(len(yaxes)))
      self.set_axis_title(yaxes[0], name, char, unit)

  def clear_axis_title(self, direc="xy"):
    """
    Method to clear axis title.
    """
    for d in direc:

      for axis in (k for k in self._axes.keys() if k.startswith(d)):
        self.set_axis_title(axis)

      if "annotations" in self.layout:
        self.layout.annotations = tuple(
          a for a in self.layout.annotations
          if "name" not in a or a.name != d+"-title")

  def set_axis_range(self, axis, minimum=None, maximum=None):
    """
    Method to set range of an axis.
    """
    if axis in self._axes and minimum is None or maximum is None:
      self._axes[axis].delete_layout("range")
    else:
      self.set_axis_layout(axis, "range", [minimum, maximum])

  def set_x_range(self, minimum=None, maximum=None):
    self.set_axis_range("x\d*", minimum, maximum)

  def set_y_range(self, minimum=None, maximum=None):
    self.set_axis_range("y\d*", minimum, maximum)

  def set_axis_ticks(self, axis, interval, num_minor=5):
    """
    Method to set ticks.
    - `interval`: distance between two consecutive major ticks.
    - `num_minor`: # of minor ticks per major tick.
    """
    self.set_axis_layout(
      axis, "dtick", interval, minor_val=interval/num_minor)

  def set_x_ticks(self, interval, num_minor=5):
    self.set_axis_ticks("x\d*", interval, num_minor)

  def set_y_ticks(self, interval, num_minor=5):
    self.set_axis_ticks("y\d*", interval, num_minor)

  def set_axis_layout(self, axis, key, value, **kwargs):
    """
    Set axis layout. `axis` can be a regular expression.
    """
    if re.match("[xyz]\d*$", axis):
      if len(axis) == 2 and axis[1] == "1":  # x1/y1 should be x/y
        axis = axis[0]
      if axis not in self._axes:
        self._create_axis(axis)
        print("New axis has been created: {}".format(axis))
      self._axes[axis].set_layout(key, value, **kwargs)
    else:
      for k, v in self._axes.items():
        if re.match(axis, k):
          v.set_layout(key, value, **kwargs)

  # Private Methods ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  # Initialization/Creation --------------------------------------------

  def _init_layout(self):
    """
    Method to initialize the layout by merging *static* `default_layout`
    into *super* `self._layout`.
    """
    self._layout = merged_dict(type(self).default_layout, self._layout)

  def _init_axis(self):
    """
    Method to initialize settings for axis.
    """
    self._axes = {}

    for k in self._layout.keys():
      if re.match("[xyz]axis\d*$", k):
        self._create_axis(k.replace("axis", ""))

    if "xaxis" not in self._layout:
      self._create_axis("x")

    if "yaxis" not in self._layout:
      self._create_axis("y")

  # Layout -------------------------------------------------------------

  def _layout_all(self, **kwargs):
    """
    Method to format all traces.
    """
    dct = co.defaultdict(list)

    for d in self.data:
      if isinstance(d, pltgo.Scatter):
        dct["scatter"].append(d)
      elif isinstance(d, pltgo.Heatmap):
        dct["heatmap"].append(d)
      else:
        raise TypeError("Non supported data type: {}".format(type(d)))

    if "scatter" in dct:
      self._layout_scatter(dct["scatter"], **kwargs)
    if "heatmap" in dct:
      self._layout_heatmap(dct["heatmap"], **kwargs)

  def _layout_scatter(self, scatters, **kwargs):
    """
    Method to format *Scatter* plots.
    """
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
          minimum = min(min(s[axis[0]]) for s in scatters)
          maximum = max(max(s[axis[0]]) for s in scatters)
          # set padding in y direction only
          padding = 0 if axis[0] == "x" else 0.05 * (maximum - minimum)
          self._extend_axis_range(axis, minimum-padding, maximum+padding)

        if not skip_ticks_setting[axis]:
          self.set_axis_ticks(
            axis, *self._auto_axis_ticks(self._axes[axis].layout["range"]))

      self._add_dummy_traces(axis_pair, self.add_scatter)

    if self._range_alignment:
      self._align_subplots_range()

  def _layout_heatmap(self, heatmaps, auto_size=True, **kwargs):
    """
    Method to format *Heatmap* plots.
    """
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
          self.set_axis_ticks(
            axis, *self._auto_axis_ticks(self._axes[axis].layout["range"]))

        self._axes[axis].set_layout("ticks", "outside")
        self._axes[axis].set_layout("constrain", "domain")

      self._axes[axis_pair[1]].layout["scaleanchor"] = axis_pair[0]

      self._add_dummy_traces(axis_pair, self.add_heatmap)

    if self._range_alignment:
      self._align_subplots_range()

  # Dummy Traces -------------------------------------------------------

  def _add_dummy_traces(self, axis_pair, callback):
    """
    Method to add dummy trances required to show mirror and minor ticks.
    """
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
    """
    Method to delete all trances of which 'uid' is in `self._dummy_uids`.
    """
    prev_len = len(self.data)

    self.data = tuple(
      d for d in self.data if d.uid not in self._dummy_uids)

    if prev_len - len(self.data) == len(self._dummy_uids):
      self._dummy_uids.clear()
    else:
      raise RuntimeError("Dummy trace might be deleted accidentally")

  # Subplots -----------------------------------------------------------

  def _make_subplots(self, trace_array, share, **kwargs):
    """
    Method to make subplots using `plotly.tools.make_subplots()`.
    """
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

    kwargs["horizontal_spacing"] = (
      0.1 if kwargs["shared_yaxes"] else 0.2) / n_col
    kwargs["vertical_spacing"] = (
      0.1 if kwargs["shared_xaxes"] else 0.3) / n_row

    fig = tools.make_subplots(rows=n_row, cols=n_col, **kwargs)

    # store axis layout of created Figure instance
    axis_layouts = {
      k.replace("axis", ""): v
      for k, v in fig._layout.items() if re.match("[xyz]axis\d*$", k)
    }

    # set subplot titles
    if "annotations" in fig.layout:
      for annotation in fig.layout.annotations:
        annotation["font"] = self._layout["titlefont"]
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
            self._axes[axis].append_mirror_axis(self._layout, **tmp_layout)
            self._axes[axis].append_minor_axis(self._layout, **tmp_layout)

      flatten_array = flatten_row + flatten_array

    return flatten_array

  def _compare_grid(self, grid1, grid2):
    """
    Compare shapes of two grids, and return True if they are equivalent.
    """
    for row1, row2 in zip(grid1, grid2):
      for cell1, cell2 in zip(row1, row2):
        if (cell1 is None) != (cell2 is None):
          return False
    return True

  def _get_grid_shape(self, grid):
    """
    Check shape of the given `grid`, and return the number of its rows
    and columns.
    """
    n_row = len(grid)
    n_col = len(grid[0])
    if not all(len(row) == n_col for row in grid):
      raise RuntimeError("Invalid shape of subplot grid")

    return n_row, n_col

  def _subplots_range_alignment(self, align):
    """
    Method to make settings to align subplots.
    """
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
    """
    Method to align axis range of subplots.
    """
    for k, v in self._range_alignment.items():
      minimum = min(self._axes[axis].layout["range"][0] for axis in v)
      maximum = max(self._axes[axis].layout["range"][1] for axis in v)
      self.set_axis_range(k, minimum, maximum)
      self.set_axis_ticks(
        k, *self._auto_axis_ticks(self._axes[k].layout["range"]))

  def _append_range_alignment(self, master, axis):
    """
    Method to append new axis to `self._range_alignment`.
    """
    if master in self._range_alignment:
      self._range_alignment[axis] = self._range_alignment[master]
      self._range_alignment[axis].append(axis)
    elif master == axis:
      self._range_alignment[axis] = [axis]
    else:
      raise RuntimeError("Invalid range alignment")

  def _show_range_alignment(self):
    """
    Method to show `self._range_alignment`.
    """
    if self._range_alignment:
      print("reference for range alignment:")

    for k, v in self._range_alignment.items():
      print("{:3s}: min/max of {}".format(k,v))

  def _show_subplot_grid(self, subplots):
    """
    Method to show axis pair corresponding to each subplot grid.
    """
    print("subplot grid:")

    maxlen = max(len(s) for s in sum(subplots, []))

    for row in subplots:
      print("| {} |".format(" | ".join(
        format(s, "^{}s".format(maxlen)) for s in row)))

  # Axis Management ----------------------------------------------------

  def _create_axis(self, axis, **kwargs):
    """
    Method to create an instance of MirroredAxisWithMinorTick.
    """
    self._axes[axis] = MirroredAxisWithMinorTick(axis, self._layout, **kwargs)

  def _clear_axes(self):
    """
    Remove all axis layouts.
    """
    self._axes.clear()
    axis_layout_keys = [
      k for k in self._layout.keys() if re.match("[xyz]axis\d*$", k)]
    for k in axis_layout_keys:
      del self._layout[k]

  def _make_axis_title_string(self, name, char=None, unit=None):
    """
    Method to make a title string.
    """
    title = str(name)

    if char is not None:

      for c in type(self).unitalicized:  # `1 < len(c)` is OK.
        char = char.replace(c, "</i>{}<i>".format(c))

      title += ", <i>{}</i>".format(char)

    if unit is not None:
      title += " [{}]".format(unit)

    return title

  def _extend_axis_range(self, axis, minimum, maximum):
    """
    Method to extend range of the given axis. If the range has not
    been set yet, `minimum` and `maximum` will be set as it is.
    """
    if self._axes[axis].in_layout("range"):
      self.set_axis_range(
        axis,
        min(minimum, self._axes[axis].layout["range"][0]),
        max(maximum, self._axes[axis].layout["range"][1]))
    else:
      self.set_axis_range(axis, minimum, maximum)

  def _auto_axis_ticks(self, axis_range):
    """
    Method to automatically determine `interval` and `num_minor` for
    `self._set_axis_ticks`.
    - `length`: distance from the minimum to maximum of the axis range.
    """
    tmpd = (axis_range[1]-axis_range[0])/3  # at least 3 tick labels
    order = int(np.floor(np.log10(tmpd)))
    scaled = tmpd/(10**order)

    if 5 < scaled:
      return 5*10**order, 5
    elif 2 < scaled:
      return 2*10**order, 4
    else:
      return 10**order, 5

  def _set_global_x_title(self, title):
    """
    Method to set a title of x axis using `self.layout.annotations`.
    This title is a global one for all subplots.
    """
    title_layout = {
      "font": self._layout["titlefont"],
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

      if not found:
        self.layout.annotations += (title_layout,)

    else:
      self.layout.annotations = (title_layout,)

  def _set_global_y_title(self, title):
    """
    Method to set a title of y axis using `self.layout.annotations`.
    This title is a global one for all subplots.
    """
    title_layout = {
      "font": self._layout["titlefont"],
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

      if not found:
        self.layout.annotations += (title_layout,)

    else:
      self.layout.annotations = (title_layout,)

  # Miscellaneous ------------------------------------------------------

  def _set_data(self, data):
    """
    Method to set `self.data`.
    - `data` should be a list of trace instances.
    """
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

  # `mirror="ticks"` cannot be used,
  # because mirroring ticks breaks auto margin (for labeled axis).
  main_default_layout = {
    **cp.deepcopy(common_default_layout),
    "titlefont": {
      "family": "Arial",
      "size": 20,
    },
    "showline": False,
    "showticklabels": True,
    "ticklen": 5,
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
    """
    Initializer of MirroredAxisWithMinorTick class.
    Note that `self.layout` of this class is NOT an instance of
    `plotly.graph_objs.Layout`, but just a Python dictionary.
    """
    self.name = axis

    self.direc = axis[0]
    self.index = int(axis[1:]) if 1 < len(axis) else 1

    layout_key = "{}axis{}".format(
      self.direc, self.index if 1 < self.index else "")

    self.layout = parent_layout[layout_key] = merged_dict(
      type(self).main_default_layout, parent_layout[layout_key]
      if layout_key in parent_layout else {})

    # ensure confort space between tick labels and axis line
    if self.direc == "y":
      self.layout["tickprefix"] = "\u2009"
      self.layout["ticksuffix"] = "\u2009"

    if "anchor" not in kwargs:
      kwargs["anchor"] = type(self).opposite[self.direc] + self.name[1:]

    self.layout.update(**kwargs)

    self.mirrors = []
    self.minors = []
    self._mirror_layouts = []
    self._minor_layouts = []

    self.append_mirror_axis(parent_layout, **kwargs)
    self.append_minor_axis(parent_layout, **kwargs)

  def delete_layout(self, key):
    if key in self.layout:
      del self.layout[key]
    for mirror_layout in self._mirror_layouts:
      if key in mirror_layout:
        del mirror_layout[key]
    for minor_layout in self._minor_layouts:
      if key in minor_layout:
        del minor_layout[key]

  def set_layout(self, key, val, mirror_val=None, minor_val=None):
    if mirror_val is None: mirror_val = val
    if minor_val is None: minor_val = val
    self.layout[key] = val
    for mirror_layout in self._mirror_layouts:
      mirror_layout[key] = mirror_val
    for minor_layout in self._minor_layouts:
      minor_layout[key] = minor_val

  def in_layout(self, key):
    return all(
      key in layout for layout in [
        self.layout, *self._mirror_layouts, *self._minor_layouts])

  def append_mirror_axis(self, parent_layout, **kwargs):

    mirror_index = 100 * (2*len(self._mirror_layouts)+1) + self.index

    mirror_layout_key = "{}axis{}".format(self.direc, mirror_index)

    mirror_layout = parent_layout[mirror_layout_key] = merged_dict(
      type(self).mirror_default_layout, parent_layout[mirror_layout_key]
      if mirror_layout_key in parent_layout else {})

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

  def append_minor_axis(self, parent_layout, **kwargs):

    minor_index = 100 * (2*len(self._minor_layouts)+2) + self.index

    minor_layout_key = "{}axis{}".format(self.direc, minor_index)

    minor_layout = parent_layout[minor_layout_key] = merged_dict(
      type(self).minor_default_layout, parent_layout[minor_layout_key]
      if minor_layout_key in parent_layout else {})

    minor_layout["overlaying"] = self.name
    minor_layout["scaleanchor"] = self.name

    minor_layout.update(**kwargs)

    self.minors.append("{}{}".format(self.direc, minor_index))
    self._minor_layouts.append(minor_layout)
