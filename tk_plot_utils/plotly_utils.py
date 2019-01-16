import re
import copy as cp
import numpy as np
import collections as coll

from plotly import tools

from .plotly_override import  plt, pltgo
from .utility_functions import merged_dict

#=======================================================================

def make_subplots(scale=1.0, *args, **kwargs):
  """
  Static method to interface with `plotly.tools.make_subplots`.
  """
  tmp = ExtendedFigureWidget(tools.make_subplots(*args, **kwargs))

  if "annotations" in tmp._layout:
    for annotation in tmp._layout["annotations"]:
      annotation["font"] = cp.deepcopy(tmp._layout["titlefont"])

  return tmp

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
      #"t": 80,
    }
  }

  unitalicize=["(", ")", "sin", "cos", "tan", "exp", "log"]

  def __init__(self, *args, **kwargs):
    """
    Initializer of ExtendedFigureWidget class.
    """
    super().__init__(*args, **kwargs)

    self._init_layout(cp.deepcopy(self._layout))
    self._init_axis(cp.deepcopy(self._layout))

    self._dummy_uids = []

  def assign_subplot(self, figure, *args, **kwargs):
    """
    Method to assign traces contained in `figure` to a specified subplot
    using `plotly.graph_objs.FigureWidget.append_trace`.
    """
    for trace in figure.data:
      self.append_trace(trace, *args, **kwargs)

  def scatter(self, data, **kwargs):
    """
    Method to create `plotly.graph_objs.Scatter` instance(s) from `dict`
    (`list`/`tuple` of `dict`) and add it (them) to this instance.
    """
    self.data = tuple()
    return self.append_scatter(data, **kwargs)

  def append_scatter(self, data, **kwargs):
    """
    Method to create `plotly.graph_objs.Scatter` instance(s) from `dict`
    (`list`/`tuple` of `dict`) and add it (them) to this instance.
    """
    self._scatter(data, **kwargs)
    return self

  def heatmap(self, data, **kwargs):
    """
    Method to create `plotly.graph_objs.Heatmap` instance(s) from `dict`
    (`list`/`tuple` of `dict`) and add it (them) to this instance.
    """
    self.data = tuple()
    return self.append_heatmap(data, **kwargs)

  def append_heatmap(self, data, **kwargs):
    """
    Method to create `plotly.graph_objs.Heatmap` instance(s) from `dict`
    (`list`/`tuple` of `dict`) and add it (them) to this instance.
    """
    self._heatmap(data, **kwargs)
    return self

  def show(self, data=None, plot="scatter", download=True, **kwargs):
    """
    Method to show a plot of data contained in this instance.
    """
    if data is not None:
      if plot == "scatter":
        self._scatter(data, **kwargs)
      elif plot == "heatmap":
        self._heatmap(data, **kwargs)
      else:
        raise ValueError("Unrecognized plot type: {}".format(plot))

    dct = coll.defaultdict(list)

    for i, d in enumerate(self._data):
      dct[d["type"]].append(self.data[i])

    if "scatter" in dct:
      self._layout_scatter(dct["scatter"], **kwargs)
    if "heatmap" in dct:
      self._layout_heatmap(dct["heatmap"], **kwargs)

    # plotting

    auto_kwargs = {
      "show_link": False,
      "image": "svg" if download else None,
      "image_width": self._layout["width"],
      "image_height": self._layout["height"],
      "filename": "plot",
    }

    for k in list(auto_kwargs.keys()):
      if k in kwargs:
        del auto_kwargs[k]

    plt.iplot(self, **auto_kwargs, **kwargs)

    self._clear_dummy_traces()

  def set_legend(self, position=None, padding=10, **kwargs):
    """
    Method to set layout of the legend. Calling this method with no
    parameter hides the legend.
    - `position` should be one of "upper right", "lower right",
      "upper left", "lower left" and "default".
    - `padding` is distance (in px) between the legend and frame line
      of the plot (legend is inside the frame).
    - `**kwargs` will be added to `plotly.graph_objs.Layout.legend`.
    """
    self._layout["legend"] = kwargs

    if position is None:
      self._layout["showlegend"] = False

    elif not any([k in kwargs for k in ["x", "y", "xanchor", "yanchor"]]):

      xpadding = padding / self._layout["width"] # in normalized coordinates
      ypadding = padding / self._layout["height"] # in normalized coordinates

      if position == "default":
        pass
      elif position == "upper right":
        self._layout["legend"].update({
          "x": 1-xpadding,
          "xanchor": "right",
          "y": 1-ypadding,
          "yanchor": "top",
        })
      elif position == "lower right":
        self._layout["legend"].update({
          "x": 1-xpadding,
          "xanchor": "right",
          "y": ypadding,
          "yanchor": "bottom",
        })
      elif position == "upper left":
        self._layout["legend"].update({
          "x": xpadding,
          "xanchor": "left",
          "y": 1-ypadding,
          "yanchor": "top",
        })
      elif position == "lower left":
        self._layout["legend"].update({
          "x": xpadding,
          "xanchor": "left",
          "y": ypadding,
          "yanchor": "bottom",
        })
      else:
        raise ValueError("Unrecognized position: {}".format(position))

  def set_title(self, title, space=30):
    """
    Method to set a title string using `self._layout["annotations"]`.
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

    if "annotations" in self._layout:

      found = False

      for annotation in self._layout["annotations"]:
        if "name" in annotation and annotation["name"] == "title":
          found = True
          annotation["text"] = title

      if not found:
        self._layout["annotations"].append(title_layout)

    else:
      self._layout["annotations"] = [title_layout]

  def set_axis_title(
    self, axis, name, char=None, unit=None):
    """
    Method to set a string to `self._layout["*axis*"]["title"]`,
    where the wildcard `*` is determined by `axis`.
    The string is something like `"{name}, <i>{char}</i> [{unit}]"`,
    if `char` and `unit` are provided.
    """
    if axis not in self._axis:
      self._create_axis(axis)

    title = str(name)

    if char is not None:

      for c in type(self).unitalicize:  # `1 < len(c)` is OK.
        char = char.replace(c, "</i>{}<i>".format(c))

      title += ", <i>{}</i>".format(char)

    if unit is not None:
      title += " [{}]".format(unit)

    self._axis[axis].layout["title"] = title

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

  # Private Methods ----------------------------------------------------

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

  def _create_axis(self, axis):
    """
    Method to create an instance of MirroredAxisWithMinorTick.
    """
    self._axis[axis] = MirroredAxisWithMinorTick(axis, self._layout)

  def _scatter(self, data, **kwargs):
    """
    Method to create `plotly.graph_objs.Scatter` instance(s) from `dict`
    (`list`/`tuple` of `dict`) and add it (them) to this instance.
    """
    if isinstance(data, dict):
      data = [data]
    elif not isinstance(data, (list, tuple)):
      raise TypeError("Wrong type of data: {}".format(type(data)))

    for d in data:
      self.add_scatter()
      self.data[-1].update(d)

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

      # add dummy data to show mirror axis & minor ticks

      axis_names_list = [
        [self._axis[axis].mirror_name for axis in axis_pair],
        [self._axis[axis].minor_name for axis in axis_pair],
      ]

      for axis_names in axis_names_list:
        dummy = self.add_scatter()
        dummy.update({
          "visible": False,
          **{"{}axis".format(name[0]): name for name in axis_names}
        })
        self._dummy_uids.append(dummy["uid"])

  def _heatmap(self, data, **kwargs):
    """
    Method to create `plotly.graph_objs.Heatmap` instance(s) from `dict`
    (`list`/`tuple` of `dict`) and add it (them) to this instance.
    """
    if isinstance(data, dict):
      data = [data]
    elif not isinstance(data, (list, tuple)):
      raise TypeError("Wrong type of data: {}".format(type(data)))

    for d in data:

      if "transpose" not in d:
        d["transpose"] = True

      nx, ny = np.array(d["z"]).shape

      if not d["transpose"]:
        nx, ny = ny, nx

      if "x0" in d or "y0" in d:
        if "x0" in d and "y0" in d:
          d["origin"] = (d["x0"], d["y0"])
          print("Values of 'x0' and 'y0' are used for 'origin'")
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

      self.add_heatmap()
      self.data[-1].update(d)

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

      # add dummy data to show mirror axis & minor ticks

      axis_names_list = [
        [self._axis[axis].mirror_name for axis in axis_pair],
        [self._axis[axis].minor_name for axis in axis_pair],
      ]

      for axis_names in axis_names_list:
        dummy = self.add_heatmap()
        dummy.update({
          "visible": False,
          **{"{}axis".format(name[0]): name for name in axis_names}
        })
        self._dummy_uids.append(dummy["uid"])

      # change plot size if the heatmap is single

      if len(dct) == 1 and auto_size:
        if nx > ny:
          self._layout["width"] = (nx/ny) * self._layout["height"]
        else:
          self._layout["height"] = (ny/nx) * self._layout["width"]

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

  def _auto_axis_ticks(self, axis_range):
    """
    Method to automatically determine `interval` and `num_minor` for
    `self._set_axis_ticks`.
    - `length`: distance from the minimum to maximum of the axis range.
    """
    tmpd = (axis_range[1]-axis_range[0])/5
    log10 = np.log10(tmpd)
    order = int(log10)
    scaled = tmpd/(10**order)

    if 7.5 < scaled:
      return 10**(order+1), 10
    elif 3.5 < scaled:
      return 5*10**order, 5
    elif 1.5 < scaled:
      return 2*10**order, 2
    else:
      return 10**order, 10

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
    "showline": True, # only one axis may show line
    "showticklabels": False,
    "ticklen": 3,
    "mirror": "ticks",
  }

  opposite = {"x": "y", "y": "x"}
  mirror_side = {"x": "top", "y": "right"}

  def __init__(self, axis, parent_layout, *args, **kwargs):
    """
    Initializer of MirroredAxisWithMinorTick class.
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

  def __repr__(self):
    return self.name

  def delete_layout(self, key):
    del self.layout[key]
    del self.mirror_layout[key]
    del self.minor_layout[key]

  def set_layout(self, key, val, mirror_val=None, minor_val=None):
    self.layout[key] = val
    self.mirror_layout[key] = val if mirror_val is None else mirror_val
    self.minor_layout[key] = val if minor_val is None else minor_val

  def in_layout(self, key):
    return all(
      key in layout
      for layout in [self.layout, self.mirror_layout, self.minor_layout])