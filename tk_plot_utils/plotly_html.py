"""Submodule associated with HTML objects containing javascript functions."""

import os
import pkgutil

import IPython.display as ipd

import plotly.offline as plt
import plotly.graph_objs as pltgo

# ----------------------------------------------------------------------

initial_html = """\
<script>
  function download_plotly_image(plot_id, format, height, width, filename)
  {
    let p = document.getElementById(plot_id);
    window._Plotly.downloadImage(
      p,
      {
        format: format,
        height: height,
        width: width,
        filename: filename
      });
  };
</script>
"""

# hide all draggable elements except for those belonging to main axis
initial_html += """\
<script>
  function hide_draggable_elements(plot_id)
  {
    let p = document.getElementById(plot_id);
    let svg = p.querySelector("svg.main-svg");
    let svgNS = svg.namespaceURI;
    let hidelayer = document.createElementNS(svgNS, "g");
    hidelayer.setAttribute("class", "hidelayer");
    [...p.querySelectorAll("g.draglayer > g")].forEach((item) =>
      {
        if (6 < item.getAttribute("class").length)
        {
          [...item.querySelectorAll("rect.drag")].forEach((item) =>
            {
              let rect = document.createElementNS(svgNS, "rect");
              for (let key of ["style", "x", "y", "width", "height"])
              {
                rect.setAttribute(key, item.getAttribute(key));
              }
              hidelayer.appendChild(rect);
            });
        }
      });
    svg.appendChild(hidelayer);
  };
</script>
"""

# remove Autoscale button because it dose not work well for layered ticks
initial_html += """\
<script>
  function remove_autoscale_button(plot_id)
  {
    [...document.getElementById(plot_id).querySelectorAll("a.modebar-btn")]
      .forEach((item) =>
        {
          if (item.getAttribute("data-title") == "Autoscale")
          {
            item.parentNode.removeChild(item);
          }
        });
  };
</script>
"""

# shift x title to correct position for subplots
initial_html += """\
<script>
  function shift_subplots_xtitle(plot_id, xtitle_index)
  {
    let p = document.getElementById(plot_id);
    let xtitle = [...p.querySelectorAll("g.infolayer > g")]
      .filter((g) => g.className.baseVal == "annotation")[xtitle_index]
      .querySelector("g.cursor-pointer");
    let t = xtitle.getAttribute("transform");
    let ytrans_old = parseFloat(t.slice(t.indexOf(",")+1, t.indexOf(")")));
    let h_rect = parseFloat(xtitle.querySelector("rect").getAttribute("height"));
    let ytrans_new = p.layout.height - h_rect;
    xtitle.setAttribute("transform",
      t.slice(0,t.indexOf(",")+1) + ytrans_new.toString() + ")");
    p.layout.annotations[xtitle_index].yshift = ytrans_old - ytrans_new;
  };
</script>
"""

# shift y title to correct position for subplots
initial_html += """\
<script>
  function shift_subplots_ytitle(plot_id, ytitle_index)
  {
    let p = document.getElementById(plot_id);
    let annotation = [...p.querySelectorAll("g.infolayer > g")]
      .filter((g) => g.className.baseVal == "annotation")[ytitle_index];
    let ytitle_parent = annotation.querySelector("g.annotation-text-g");
    let ytitle = annotation.querySelector("g.cursor-pointer");
    let r = ytitle_parent.getAttribute("transform");
    let t = ytitle.getAttribute("transform");
    let xtrans_old = parseFloat(t.slice(t.indexOf("(")+1, t.indexOf(",")));
    let rect = ytitle.querySelector("rect");
    let xcenter = 0.5*parseFloat(rect.getAttribute("width"))
                  + parseFloat(rect.getAttribute("x"));
    let ycenter = 0.5*parseFloat(rect.getAttribute("height"))
                  - parseFloat(rect.getAttribute("y"));
    let xtrans_new = ycenter - xcenter;
    ytitle.setAttribute("transform",
      t.slice(0,t.indexOf("(")+1) + xtrans_new.toString() + t.slice(t.indexOf(",")));
      ytitle_parent.setAttribute("transform",
      r.slice(0,r.indexOf(",")+1) + (xtrans_new+xcenter).toString() + r.slice(r.lastIndexOf(",")));
    p.layout.annotations[ytitle_index].xshift = xtrans_new - xtrans_old;
  };
</script>
"""

# load clipboard.js (used for copying style names from reference HTML)
style_clipboard = """\
<style>
  .btn-clipboard {
    padding: 0px;
  }
</style>
"""

online_clipboard = """\
<script>
  requirejs.config({
      paths: {
        clipboard: "https://cdn.jsdelivr.net/npm/clipboard@2/dist/clipboard.min"
      }
    });
  if (!window._ClipboardJS)
  {
    require(["clipboard"], (clipboard) =>
      {
        window._ClipboardJS = clipboard;
        new window._ClipboardJS(".btn-clipboard");
      });
  }
  else
  {
    new window._ClipboardJS(".btn-clipboard");
  }
</script>
"""

offline_clipboard = """\
<script>
  if (!window._ClipboardJS)
  {{
    define("clipboard", (require, exports, module) =>
      {{
        {}
      }});
    require(["clipboard"], (ClipboardJS) =>
      {{
        window._ClipboardJS = ClipboardJS;
        new window._ClipboardJS(".btn-clipboard");
      }});
  }}
  else
  {{
    new window._ClipboardJS(".btn-clipboard");
  }}
</script>
"""

def _get_clipboardjs():
  """Return the contents of the minified clipboard.js library
  as a string."""
  path = os.path.join("package_data", "clipboard.min.js")
  return pkgutil.get_data("tk_plot_utils", path).decode("utf-8")

def init_plotly(connected=False):
  """Initialize plotly.js and some javascript functions in the browser.

  Call ``plotly.offline.init_notebook_mode()`` and display a HTML object
  defining some javascript functions.

  Parameters:

  connected: bool
    This parameter is passed to ``plotly.offline.init_notebook_mode()``.
    If True, the plotly.js library will be loaded from an online CDN.
    If False, the plotly.js library will be loaded locally
    from the plotly python package.

  """
  plt.init_notebook_mode(connected=connected)
  ipd.display(ipd.HTML(
    initial_html + style_clipboard + (
      online_clipboard
      if connected else offline_clipboard.format(_get_clipboardjs()))))

# ----------------------------------------------------------------------

import plotly.offline.offline as pltoff

# Jupyter causes "ReferenceError: Plotly is not defined"
# when downloading an image of the plot. Using `window._Plotly`
# instead of `Plotly` is a workaround for this problem.
download_html = """\
<button onclick="download_plotly_image('{plot_id}', '{format}', {height}, {width}, '{filename}')">
  Download Image as <span style="text-transform:uppercase;">{format}</span>
</button>
"""

disable_html = """\
<script>
  if (window.Jupyter)
  {{
    hide_draggable_elements("{plot_id}");
    remove_autoscale_button("{plot_id}");
  }}
  else
  {{
    window.addEventListener("load", () =>
    {{
      hide_draggable_elements("{plot_id}");
      remove_autoscale_button("{plot_id}");
    }});
  }}
</script>
"""

# shift x title for subplots
xtitle_html = """\
<script>
  if (window.Jupyter)
  {{{{
    shift_subplots_xtitle("{{plot_id}}", {0});
  }}}}
  else
  {{{{
    window.addEventListener("load", () =>
    {{{{
      shift_subplots_xtitle("{{plot_id}}", {0});
    }}}});
  }}}}
</script>
"""

# shift y title for subplots
ytitle_html = """\
<script>
  if (window.Jupyter)
  {{{{
    shift_subplots_ytitle("{{plot_id}}", {0});
  }}}}
  else
  {{{{
    window.addEventListener("load", () =>
    {{{{
      shift_subplots_ytitle("{{plot_id}}", {0});
    }}}});
  }}}}
</script>
"""

get_image_download_script_original = pltoff.get_image_download_script

def override(xtitle_index=None, ytitle_index=None):
  """Override ``plotly.offline.offline.get_image_download_script()``
  every time before plotting.

  Parameters:

  xtitle_index: None or int
    Index in the annotations corresponds to a title of *x* axis.
    None means that the title of *x* axis is not written
    in an annotation. When the title of *x* axis is written in one of
    the annotations, its index should be specified by this parameter
    and passed to a javascript function.

  ytitle_index: None or int
    Index in the annotations corresponds to a title of *y* axis.
    None means that the title of *y* axis is not written
    in an annotation. When the title of *y* axis is written in one of
    the annotations, its index should be specified by this parameter
    and passed to a javascript function.

  """

  inject_html = download_html + disable_html

  if xtitle_index is not None:
    inject_html += xtitle_html.format(xtitle_index)
  if ytitle_index is not None:
    inject_html += ytitle_html.format(ytitle_index)

  def get_image_download_script_override(caller):
    if caller == "plot":
      return get_image_download_script_original(caller)
    elif caller != "iplot":
      raise ValueError("caller should only be one of `iplot` or `plot`")

    return inject_html

  pltoff.get_image_download_script = get_image_download_script_override
