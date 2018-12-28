import plotly.offline as plt
import plotly.graph_objs as pltgo

import plotly.offline.offline as pltoff

import copy as cp
import numpy as np
import IPython.display as ipd

from notebook import notebookapp

# Jupyter causes "ReferenceError: Plotly is not defined"
# when downloading an image of the plot. Using `window._Plotly`
# instead of `Plotly` is a workaround for this problem.
download_html = """\
<button onclick="download_image('{format}', {height}, {width}, '{filename}')">
  Download Image as <span style="text-transform:uppercase;">{format}</span>
</button>
<script>
  function download_image(format, height, width, filename)
  {{
    var p = document.getElementById("{plot_id}");
    window._Plotly.downloadImage(
      p,
      {{
        format: format,
        height: height,
        width: width,
        filename: filename
      }});
  }};
</script>
"""

# remove Autoscale button because it dose not work well for minor ticks.
download_html += """\
<script>
  [...document.getElementById("{plot_id}").querySelectorAll("a.modebar-btn")]
    .forEach((item) =>
      {{
        if (item.getAttribute("data-title") == "Autoscale")
        {{
          item.parentNode.removeChild(item);
        }}
      }});
</script>
"""

get_image_download_script_original = pltoff.get_image_download_script

def get_image_download_script_override(caller):
  """
  This function overrides `plotly.offline.offline.get_image_download_script`.
  """
  if caller == "plot":
    return get_image_download_script_original(caller)
  elif caller != "iplot":
    raise ValueError("caller should only be one of `iplot` or `plot`")

  return download_html

pltoff.get_image_download_script = get_image_download_script_override

class PlotlyPlotter:
  """
  Class for setting and plotting via Plotly.
  """

  @staticmethod
  def init(*args, **kwargs):
    """
    Static method of PlotlyPlotter class. Please call this method
    before creating instances of PlotlyPlotter class.
    Since this method loads local plotly.min.js (by default),
    it takes a bit of time and notebook size will increase.
    """
    plt.init_notebook_mode(*args, **kwargs)

  def __init__(self, *args, **kwargs):
    """
    Initializer of PlotlyPlotter class.
    """
    self.object = None
    self.init_layout(**kwargs)

  def init_layout(self,
    width=640,
    height=480,
    font_family="Arial",
    font_size=20,
    tick_length=5,
    **kwargs):
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
      "hoverformat": ".f"
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

  def figure(self, data, **kwargs):
    """
    Method to create a `plotly.graph_objs.Figure` instance
    from the given data, and assign it to `self.object`.
    Note that this method returns not the created instance but `self`.
    """
    if isinstance(data, dict):
      data = [data]
    elif not isinstance(data, list):
      raise TypeError("Wrong type of data: {}".format(type(data)))

    if not all(["range" in self.layout["xaxis"+s] for s in ["", "2"]]):
      xmin = min([min(d["x"]) for d in data])
      xmax = max([max(d["x"]) for d in data])
      self.set_x_range(xmin, xmax)

    if not all(["range" in self.layout["yaxis"+s] for s in ["", "2"]]):
      ymin = min([min(d["y"]) for d in data])
      ymax = max([max(d["y"]) for d in data])
      padding = 0.05 * (ymax - ymin)
      self.set_y_range(ymin-padding, ymax+padding)

    data.append({ # this dummy data is required to show minor ticks
      "x": [], "y": [], "xaxis": "x2", "yaxis": "y2", "visible": False,
    })

    self.object = pltgo.FigureWidget({
      "data": data,
      "layout": self.layout
    })

    return self

  def heatmap(self, data, **kwargs):
    """
    Method to create a `plotly.graph_objs.Heatmap` instance
    from the given data, and assign it to `self.object`.
    Note that this method returns not the created instance but `self`.

    Array shape of 'z' should be (*Nx*, *Ny*) where *Nx* and *Ny* is
    the number of values in the *x* and *y* direction, respectively
    (This is a transpose of Plotly's default).
    """
    if not isinstance(data, dict):
      raise TypeError("Wrong type of data: {}".format(type(data)))

    if "transpose" not in data:
      data["transpose"] = True

    nx, ny = np.array(data["z"]).shape

    if not data["transpose"]:
      nx, ny = ny , nx

    if "origin" in data:

      if "x" in data:
        print("Value of 'x' will be overwritten")
      if "y" in data:
        print("Value of 'y' will be overwritten")

      dx, dy = data["dx"], data["dy"]

      xmin = data["origin"][0]
      ymin = data["origin"][1]
      xmax = xmin + nx*dx
      ymax = ymin + ny*dy

      self.set_x_range(xmin, xmax)
      self.set_y_range(ymin, ymax)

      data["x"] = xmin + np.arange(nx+1)*dx
      data["y"] = ymin + np.arange(ny+1)*dy

      del data["origin"]

    # modify layout

    self.layout["xaxis"]["ticks"] = "outside"
    self.layout["yaxis"]["ticks"] = "outside"
    self.layout["xaxis2"]["ticks"] = "outside"
    self.layout["yaxis2"]["ticks"] = "outside"

    self.layout["xaxis"]["constrain"] = "domain"
    self.layout["yaxis"]["constrain"] = "domain"
    self.layout["xaxis2"]["constrain"] = "domain"
    self.layout["yaxis2"]["constrain"] = "domain"

    self.layout["yaxis"]["scaleanchor"] = "x"

    self.object = pltgo.FigureWidget({
      "data": [
        pltgo.Heatmap(data),
        pltgo.Heatmap({ # this dummy data is required to show minor ticks
          "z": [], "xaxis": "x2", "yaxis": "y2", "visible": False,
        })],
      "layout": self.layout
    })

    return self

  def show(self, data=None, plot="figure", download=True, **kwargs):
    """
    Method to show a plot of the given data.
    If data have already been assigned to `self.object`,
    any parameter is not required.
    """
    if isinstance(data, (dict, list)):
      if plot == "figure":
        self.figure(data, **kwargs)
      elif plot == "heatmap":
        self.heatmap(data, **kwargs)
      else:
        raise ValueError("Unrecognized plot type: {}".format(plot))

    auto_kwargs = {
      "show_link": False,
      "image": "svg" if download else None,
      "image_width": self.layout["width"],
      "image_height": self.layout["height"],
      "filename": "plot",
    }

    for k in list(auto_kwargs.keys()):
      if k in kwargs:
        del auto_kwargs[k]

    if self.object is None:
      raise RuntimeError("Plot object has not been set yet")
    else:
      plt.iplot(self.object, **auto_kwargs, **kwargs)

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
    self.layout["legend"] = kwargs

    if position is None:
      self.layout["showlegend"] = False

    elif not any([k in kwargs for k in ["x", "y", "xanchor", "yanchor"]]):

      xpadding = padding / self.layout["width"] # in normalized coordinates
      ypadding = padding / self.layout["height"] # in normalized coordinates

      if position == "default":
        pass
      elif position == "upper right":
        self.layout["legend"].update({
          "x": 1-xpadding,
          "xanchor": "right",
          "y": 1-ypadding,
          "yanchor": "top",
        })
      elif position == "lower right":
        self.layout["legend"].update({
          "x": 1-xpadding,
          "xanchor": "right",
          "y": ypadding,
          "yanchor": "bottom",
        })
      elif position == "upper left":
        self.layout["legend"].update({
          "x": xpadding,
          "xanchor": "left",
          "y": 1-ypadding,
          "yanchor": "top",
        })
      elif position == "lower left":
        self.layout["legend"].update({
          "x": xpadding,
          "xanchor": "left",
          "y": ypadding,
          "yanchor": "bottom",
        })
      else:
        raise ValueError("Unrecognized position: {}".format(position))

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