import plotly.offline as plt
import plotly.graph_objs as pltgo
import plotly.offline.offline as pltoff

#-----------------------------------------------------------------------

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

# remove Autoscale button because it dose not work well for minor ticks
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
