import plotly.offline as plt
import plotly.graph_objs as pltgo

import os

import copy as cp
import IPython.display as ipd

from notebook import notebookapp

class PlotlyPlotter:
  """
  Class for setting and plotting.
  """

  def __init__(self, *args, **kwargs):
    """
    Initializer of PlotlyPlotter class.
    """
    plt.init_notebook_mode()

    self.init_layout(**kwargs)

  def init_layout(self,
    width=640,
    height=480,
    font_family="Arial",
    font_size=20,
    tick_length=5):
    """
    Method to initialize layout dictionary.
    """
    axis = {
      "titlefont": {
        "family": font_family,
        "size": font_size,
      },
      "zeroline": False,
      "showgrid": False,
      "showline": True,
      "showticklabels": True,
      "ticks": "inside",
      "ticklen": tick_length,
      "mirror": "ticks",
    }

    minor_tick_axis = {
      "zeroline": False,
      "showgrid": False,
      "showline": False,
      "showticklabels": False,
      "ticks": "inside",
      "ticklen": tick_length*0.6,
      "mirror": "ticks",
    }

    self.layout = {
      "width": width,
      "height": height,
      "font": {
        "family": font_family,
        "size": font_size*0.9,
      },
      "titlefont": {
        "family": font_family,
        "size": font_size,
      },
      "xaxis": cp.deepcopy(axis),
      "xaxis2": cp.deepcopy(minor_tick_axis),
      "yaxis": cp.deepcopy(axis),
      "yaxis2": cp.deepcopy(minor_tick_axis),
    }

    self.layout["xaxis2"]["overlaying"] = "x"
    self.layout["xaxis2"]["scaleanchor"] = "x"
    self.layout["yaxis2"]["overlaying"] = "y"
    self.layout["yaxis2"]["scaleanchor"] = "y"

  def create_figure(self, data):
    """
    Method to create a `plotly.graph_objs.FigureWidget` instance
    from the given data and `self.layout`.
    """
    if not isinstance(data, list) and not isinstance(data, tuple):
      data = [data]

    if not all(["range" in self.layout["xaxis"+s] for s in ["", "2"]]):
      xmin = min([min(d["x"]) for d in data])
      xmax = max([max(d["x"]) for d in data])
      self.set_x_range(xmin, xmax)

    if not all(["range" in self.layout["yaxis"+s] for s in ["", "2"]]):
      ymin = min([min(d["y"]) for d in data])
      ymax = max([max(d["y"]) for d in data])
      padding = 0.05 * (ymax - ymin)
      self.set_y_range(ymin-padding, ymax+padding)

    data.append({  # this dummy data is required to show minor ticks
      "x": [], "y": [], "xaxis": "x2", "yaxis": "y2", "visible": False,
    })

    return pltgo.FigureWidget({"data": data, "layout": self.layout})

  def show(self, data, **kwargs):
    """
    Method to show a plot of the given data.
    """
    plt.iplot(self.create_figure(data), **kwargs)

  def save(self, data, **kwargs):
    """
    Method to show a plot of the given data.
    """
    auto_kwargs = {
      "show_link": False,
      "image_width": self.layout["width"],
      "image_height": self.layout["height"],
    }

    for k in list(auto_kwargs.keys()):
      if k in kwargs:
        del auto_kwargs[k]

    path = plt.plot(self.create_figure(data), **auto_kwargs, **kwargs)

    server_list = [
      server for server in notebookapp.list_running_servers()
      if server["notebook_dir"] in path
    ]

    if len(server_list) > 0:
      if len(server_list) > 1:
        print("There are multiple candidates:")

      ipd.display(ipd.HTML("</br>".join([
        """<a href="{0}" target="_blank">{0}</a>""".format(
          s["url"] + "files" + path.split(s["notebook_dir"], 1)[1])
        for s in server_list
      ])))

    else:
      print("Image file has been saved outside Jupyter:", path)

  def set_title(self, title):
    """
    Method to set a string to `self.layout["title"]`.
    """
    self.layout["title"] = title

  def set_x_title(self, name, char=None, unit=None):
    """
    Method to set a string to `self.layout["xaxis"]["title"]`.
    The string is something like `"{name}, <i>{char}</i> [{unit}]"`,
    if `char` and `unit` are provided.
    """
    self._set_axis_title("x", name, char, unit)

  def set_y_title(self, name, char=None, unit=None):
    """
    Method to set a string to `self.layout["yaxis"]["title"]`.
    The string is something like `"{name}, <i>{char}</i> [{unit}]"`,
    if `char` and `unit` are provided.
    """
    self._set_axis_title("y", name, char, unit)

  def set_x_ticks(self, interval, num_minor=5):
    """
    Method to set ticks of x axis.
    - `interval`: distance between two consecutive major ticks.
    - `num_minor`: # of minor ticks per major tick.
    """
    self._set_axis_ticks("x", interval, num_minor)

  def set_y_ticks(self, interval, num_minor=5):
    """
    Method to set ticks of y axis.
    - `interval`: distance between two consecutive major ticks.
    - `num_minor`: # of minor ticks per major tick.
    """
    self._set_axis_ticks("y", interval, num_minor)

  def set_x_range(self, minimum=None, maximum=None):
    """
    Method to set range of the x axis.
    """
    self._set_axis_range("x", minimum, maximum)

  def set_y_range(self, minimum=None, maximum=None):
    """
    Method to set range of the y axis.
    """
    self._set_axis_range("y", minimum, maximum)

  # Private Methods

  def _set_axis_title(self, axis, name, char=None, unit=None):
    """
    Method to set a string to `self.layout["*axis"]["title"]`,
    where the wildcard `*` is determined by `axis`.
    The string is something like `"{name}, <i>{char}</i> [{unit}]"`,
    if `char` and `unit` are provided.
    """
    key = "{}axis".format(axis)

    self.layout[key]["title"] = str(name)

    if char is not None:
      self.layout[key]["title"] += ", <i>{}</i>".format(char)

    if unit is not None:
      self.layout[key]["title"] += " [{}]".format(unit)

  def _set_axis_ticks(self, axis, interval, num_minor=5):
    """
    Method to set ticks.
    - `interval`: distance between two consecutive major ticks.
    - `num_minor`: # of minor ticks per major tick.
    """
    key = "{}axis".format(axis)

    self.layout[key]["dtick"] = interval
    self.layout[key+"2"]["dtick"] = interval/num_minor

  def _set_axis_range(self, axis, minimum=None, maximum=None):
    """
    Method to set range of an axis.
    """
    key = "{}axis".format(axis)

    if minimum is None or maximum is None:
      del self.layout[key]["range"]
      del  self.layout[key+"2"]["range"]
    else:
      self.layout[key]["range"] = [minimum, maximum]
      self.layout[key+"2"]["range"] = [minimum, maximum]