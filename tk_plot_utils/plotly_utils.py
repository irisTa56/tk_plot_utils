import re
import copy as cp
import numpy as np
import collections as coll

from .plotly_override import  plt, pltgo
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
      "b": 10,
      "l": 10,
      "r": 10,
    }
  }

  unitalicized = ["(", ")", "sin", "cos", "tan", "exp", "log"]

  def __init__(self, *args, **kwargs):
    """
    Initializer of ExtendedFigureWidget class.
    """
    super().__init__(*args, **kwargs)

    self._init_layout(cp.deepcopy(self._layout))
    self._init_axis(cp.deepcopy(self._layout))

    # required to delete dummy data used for showing mirror/minor axis
    self._dummy_uids = []

    # required to align axis range in subplots
    self._range_alignment = {}

  def show(self, data=None, download=True, **kwargs):
    """
    Method to show a plot of data contained in this instance.
    """
    if data is not None:
      self._set_data(data)

    self._layout_all(**kwargs)

    auto_kwargs = {
      "show_link": False,
      "image": "svg" if download else None,
      "image_width": self.layout.width,
      "image_height": self.layout.height,
      "filename": "plot",
    }

    for k in list(auto_kwargs.keys()):
      if k in kwargs:
        del auto_kwargs[k]

    plt.iplot(self, **auto_kwargs, **kwargs)

    self._clear_dummy_traces()

  def subplots(
    self, trace_array, align={}, **kwargs):
    """
    Method to make subplots from an array of trace instances.
    - `align` is a dictionary of which keys are 'row' or 'col'
      and values are 'each' or 'all'.
      - `align={'row': 'each'}` leads to that initial range of 'y*'
      ('*' is a wild card) axes in each row will be aligned.
      - `align={'col': 'all'}` leads to that initial range of all 'x*'
      axes will be aligned.
    """
    subplots, subplots_repr, flatten_array = self._subplots(trace_array)

    if align:
      self._subplots_range_alignment(subplots, align)

    self.layout.grid = {
      "subplots": subplots_repr,
      **kwargs
    }

    self._set_data(flatten_array)

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
      "font": cp.deepcopy(self._layout["titlefont"]),
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

    # NOTE: Since `self.layout.annotations` is immutable,
    # `self._layout["annotations"]` should be used.
    if "annotations" in self._layout:

      found = False

      for annotation in self._layout["annotations"]:
        if "name" in annotation and annotation["name"] == "title":
          found = True
          annotation["text"] = title
          annotation["yshift"] = space

      if not found:
        self._layout["annotations"].append(title_layout)

    else:
      self._layout["annotations"] = [title_layout]

  def set_axis_title(
    self, axis, name=None, char=None, unit=None):
    """
    Method to set a title string to the given axis.
    The string is something like `"{name}, <i>{char}</i> [{unit}]"`,
    if `char` and `unit` are provided.
    """
    if axis not in self._axis:
      self._create_axis(axis)

    if name is None and char is None and unit is None:
      self._axis[axis].delete_layout("title")
    else:
      title = str(name)

      if char is not None:

        for c in type(self).unitalicized:  # `1 < len(c)` is OK.
          char = char.replace(c, "</i>{}<i>".format(c))

        title += ", <i>{}</i>".format(char)

      if unit is not None:
        title += " [{}]".format(unit)

      self._axis[axis].layout["title"] = title

  def set_x_title(self, name=None, char=None, unit=None):
    """
    Method wrapping `self.set_axis_title()`.
    """
    if "grid" in self._layout:
      for bottom_plot in self.layout.grid.subplots[-1]:
        self.set_axis_title(
          bottom_plot.split("y")[0], name, char, unit)
    else:
      self.set_axis_title("x", name, char, unit)

  def set_y_title(self, name=None, char=None, unit=None):
    """
    Method wrapping `self.set_axis_title()`.
    """
    if "grid" in self._layout:
      for left_plot in [row[0] for row in self.layout.grid.subplots]:
        self.set_axis_title(
          "y"+left_plot.split("y")[1], name, char, unit)
    else:
      self.set_axis_title("y", name, char, unit)

  def clear_axis_title(self, direc="xy"):
    """
    Method to clear axis title.
    """
    for d in direc:
      for axis in (k for k in self._axis.keys() if k.startswith(d)):
        self.set_axis_title(axis)

  def set_axis_range(self, axis, minimum=None, maximum=None):
    """
    Method to set range of an axis.
    """
    if axis not in self._axis:
      self._create_axis(axis)

    if minimum is None or maximum is None:
      self._axis[axis].delete_layout("range")
    else:
      self._axis[axis].set_layout("range", [minimum, maximum])

  def set_x_range(self, minimum=None, maximum=None):
    """
    Method wrapping `self.set_axis_range()`.
    """
    for axis in (k for k in self._axis.keys() if k.startswith("x")):
      self.set_axis_range(axis, minimum, maximum)

  def set_y_range(self, minimum=None, maximum=None):
    """
    Method wrapping `self.set_axis_range()`.
    """
    for axis in (k for k in self._axis.keys() if k.startswith("y")):
      self.set_axis_range(axis, minimum, maximum)

  def set_axis_ticks(self, axis, interval, num_minor=5):
    """
    Method to set ticks.
    - `interval`: distance between two consecutive major ticks.
    - `num_minor`: # of minor ticks per major tick.
    """
    if axis not in self._axis:
      self._create_axis(axis)

    self._axis[axis].set_layout(
      "dtick", interval, minor_val=interval/num_minor)

  def set_x_ticks(self, interval, num_minor=5):
    """
    Method wrapping `self.set_axis_ticks()`.
    """
    for axis in (k for k in self._axis.keys() if k.startswith("x")):
      self.set_axis_ticks(axis, interval, num_minor)

  def set_y_ticks(self, interval, num_minor=5):
    """
    Method wrapping `self.set_axis_ticks()`.
    """
    for axis in (k for k in self._axis.keys() if k.startswith("y")):
      self.set_axis_ticks(axis, interval, num_minor)

  # Private Methods ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  # Initialization/Creation --------------------------------------------

  def _init_layout(self, _layout):
    """
    Method to initialize the layout by merging *static* `default_layout`
    and *super* `self._layout`.
    """
    self._layout = merged_dict(type(self).default_layout, _layout)

  def _init_axis(self, _layout):
    """
    Method to initialize settings for axis.
    """
    self._axis = {}

    for k in _layout.keys():
      if re.search("^[xyz]axis\d*", k):
        self._create_axis(k.replace("axis", ""))

    if "xaxis" not in _layout:
      self._create_axis("x")

    if "yaxis" not in _layout:
      self._create_axis("y")

  def _create_axis(self, axis):
    """
    Method to create an instance of MirroredAxisWithMinorTick.
    """
    self._axis[axis] = MirroredAxisWithMinorTick(axis, self._layout)

  # Layout -------------------------------------------------------------

  def _layout_all(self, **kwargs):
    """
    Method to format all traces.
    """
    dct = coll.defaultdict(list)

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

    dct = coll.defaultdict(list)

    for scatter in scatters:

      axis_pair = (
        scatter.xaxis if scatter.xaxis else "x",
        scatter.yaxis if scatter.yaxis else "y")

      for axis in axis_pair:
        if axis not in self._axis:
          self._create_axis(axis)

      dct[axis_pair].append(scatter)

    # setting for each axis

    for axis_pair, scatters in dct.items():

      for axis in axis_pair:

        if not self._axis[axis].in_layout("range"):
          minimum = min(min(s[axis[0]]) for s in scatters)
          maximum = max(max(s[axis[0]]) for s in scatters)
          padding = 0 if axis[0] == "x" else 0.05 * (maximum - minimum)
          self.set_axis_range(axis, minimum-padding, maximum+padding)

        if not self._axis[axis].in_layout("dtick"):
          self.set_axis_ticks(
            axis, *self._auto_axis_ticks(self._axis[axis].layout["range"]))

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
        if axis not in self._axis:
          self._create_axis(axis)

      dct[axis_pair] = heatmap

    # setting for each axis

    for axis_pair, heatmap in dct.items():

      nx, ny = np.array(heatmap.z).shape

      if not heatmap.transpose:
        nx, ny = ny, nx

      for axis, n, v in zip(axis_pair, (nx, ny), (heatmap.x, heatmap.y)):

        if not self._axis[axis].in_layout("range"):
          minimum = v[0] if len(v) == n+1 else v[0] - 0.5*(v[1]-v[0])
          maximum = v[-1] if len(v) == n+1 else v[-1] + 0.5*(v[-1]-v[-2])
          self.set_axis_range(axis, minimum, maximum)

        if not self._axis[axis].in_layout("dtick"):
          self.set_axis_ticks(
            axis, *self._auto_axis_ticks(self._axis[axis].layout["range"]))

        self._axis[axis].set_layout("ticks", "outside")
        self._axis[axis].set_layout("constrain", "domain")
        #self._axis[axis].layout["constrain"] = "domain"

      self._axis[axis_pair[1]].layout["scaleanchor"] = axis_pair[0]

      self._add_dummy_traces(axis_pair, self.add_heatmap)

    if self._range_alignment:
      self._align_subplots_range()

  # Dummy Traces -------------------------------------------------------

  def _add_dummy_traces(self, axis_pair, callback):
    """
    Method to add dummy trances required to show mirror and minor ticks.
    """
    namepair_list = [
      tuple(self._axis[axis].mirror_name for axis in axis_pair),
      tuple(self._axis[axis].minor_name for axis in axis_pair),
    ]

    for namepair in namepair_list:
      dummy = callback()
      dummy.update({
        "visible": False,
        **{"{}axis".format(name[0]): name for name in namepair}
      })
      self._dummy_uids.append(dummy["uid"])

  def _clear_dummy_traces(self):
    """
    Method to delete all trances of which 'uid' is in `self._dummy_uids`.
    """
    while self._dummy_uids:
      uid = self._dummy_uids.pop()
      try:
        idx = [i for i, t in enumerate(self.data) if t.uid == uid][0]
        self.data = self.data[:idx] + self.data[idx+1:]
      except IndexError:
        raise RuntimeError("Dummy trace might be deleted accidentally")

  # Subplots -----------------------------------------------------------

  def _subplots(self, trace_array):
    """
    Method to make subplots arrangement from an array of trances.
    """
    counter = 0
    subplots = []
    flatten_array = []

    for row in trace_array:

      subplots_row = []

      for cell in row:

        counter += 1
        suffix = str(counter) if 1 < counter else ""
        pair = ("x"+suffix, "y"+suffix)

        for trace in cell if isinstance(cell, (list, tuple)) else [cell]:
          trace.xaxis, trace.yaxis = pair
          flatten_array.append(trace)

        for axis in pair:
          if axis not in self._axis:
            self._create_axis(axis)

        subplots_row.append(pair)

      subplots.append(subplots_row)

    subplots_repr = [["".join(pair) for pair in row] for row in subplots]

    self._show_subplot_grid(subplots_repr)

    return subplots, subplots_repr, flatten_array

  def _subplots_range_alignment(self, subplots, align):
    """
    Method to make settings to align subplots.
    """
    self._range_alignment = {}

    if "x" in align:

      if align["x"] == "each":
        master_axes = [pair[0] for pair in subplots[0]]
        for row in subplots:
          for icol, (axis, _) in enumerate(row):
            self._append_range_alignment(master_axes[icol], axis)

      elif align["x"] == "all":
        master_axis = subplots[0][0][0]
        for row in subplots:
          for axis, _ in row:
            self._append_range_alignment(master_axis, axis)

      else:
        raise RuntimeError(
          "Invalid align scheme for x: {}".format(align["x"]))

    if "y" in align:

      if align["y"] == "each":
        master_axes = [pair[1] for pair in [row[0] for row in subplots]]
        for irow, row in enumerate(subplots):
          for _, axis in row:
            self._append_range_alignment(master_axes[irow], axis)

      elif align["y"] == "all":
        master_axis = subplots[0][0][1]
        for row in subplots:
          for _, axis in row:
            self._append_range_alignment(master_axis, axis)

      else:
        raise RuntimeError(
          "Invalid align scheme for y: {}".format(align["y"]))

    self._show_range_alignment()

  def _align_subplots_range(self):
    """
    Method to align axis range of subplots.
    """
    for k, v in self._range_alignment.items():
      minimum = min(self._axis[axis].layout["range"][0] for axis in v)
      maximum = max(self._axis[axis].layout["range"][1] for axis in v)
      self.set_axis_range(k, minimum, maximum)
      self.set_axis_ticks(
        k, *self._auto_axis_ticks(self._axis[k].layout["range"]))

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

  # Miscellaneous -----------------------------------------------------------

  def _set_data(self, data):
    """
    Method to set `self.data`.
    - `data` should be a list of trace instances.
    """
    self.data = tuple()

    for d in data:
      if isinstance(d, pltgo.Scatter):
        self.add_scatter()
        self.data[-1].update(d)
      elif isinstance(d, pltgo.Heatmap):
        self.add_heatmap()
        self.data[-1].update(d)
      else:
        raise TypeError("Non supported data type: {}".format(type(d)))

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

  def __init__(self, axis, parent_layout, *args, **kwargs):
    """
    Initializer of MirroredAxisWithMinorTick class.
    Note that `self.layout` of this class is NOT an instance of
    `plotly.graph_objs.Layout`, but just a Python dictionary.
    """
    self.name = axis

    direc = axis[0]
    index = int(axis[1:]) if 1 < len(axis) else 1
    mirror_index = 100 + index  # for mirror axis
    minor_index = 200 + index  # for axis with minor ticks

    self.mirror_name = "{}{}".format(direc, mirror_index)
    self.minor_name = "{}{}".format(direc, minor_index)

    layout_key = "{}axis{}".format(direc, index if 1 < index else "")
    mirror_layout_key = "{}axis{}".format(direc, mirror_index)
    minor_layout_key = "{}axis{}".format(direc, minor_index)

    self.layout = parent_layout[layout_key] = merged_dict(
      type(self).main_default_layout, parent_layout[layout_key]
      if layout_key in parent_layout else {})

    # ensure confort space between tick labels and axis line
    if direc == "y":
      self.layout["ticksuffix"] = "\u2009"

    self.mirror_layout = parent_layout[mirror_layout_key] = merged_dict(
      type(self).mirror_default_layout, parent_layout[mirror_layout_key]
      if mirror_layout_key in parent_layout else {})

    self.mirror_layout["side"] = type(self).mirror_side[direc]
    self.mirror_layout["anchor"] = type(self).opposite[direc] + self.name[1:]
    self.mirror_layout["overlaying"] = self.name
    self.mirror_layout["scaleanchor"] = self.name

    self.minor_layout = parent_layout[minor_layout_key] = merged_dict(
      type(self).minor_default_layout, parent_layout[minor_layout_key]
      if minor_layout_key in parent_layout else {})

    self.minor_layout["anchor"] = type(self).opposite[direc] + self.name[1:]
    self.minor_layout["overlaying"] = self.name
    self.minor_layout["scaleanchor"] = self.name

  def delete_layout(self, key):
    if key in self.layout:
      del self.layout[key]
    if key in self.mirror_layout:
      del self.mirror_layout[key]
    if key in self.minor_layout:
      del self.minor_layout[key]

  def set_layout(self, key, val, mirror_val=None, minor_val=None):
    self.layout[key] = val
    self.mirror_layout[key] = val if mirror_val is None else mirror_val
    self.minor_layout[key] = val if minor_val is None else minor_val

  def in_layout(self, key):
    return all(
      key in layout
      for layout in [self.layout, self.mirror_layout, self.minor_layout])
