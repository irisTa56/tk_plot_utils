import IPython.display as ipd

import plotly.offline as plt
import plotly.graph_objs as pltgo

# ----------------------------------------------------------------------

initial_html = """\
<script>
  function download_image(plot_id, format, height, width, filename)
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

def init_plotly(*args, **kwargs):
  plt.init_notebook_mode(*args, **kwargs)
  ipd.display(ipd.HTML(initial_html))

# ----------------------------------------------------------------------

import plotly.offline.offline as pltoff

# Jupyter causes "ReferenceError: Plotly is not defined"
# when downloading an image of the plot. Using `window._Plotly`
# instead of `Plotly` is a workaround for this problem.
download_html = """\
<button onclick="download_image('{plot_id}', '{format}', {height}, {width}, '{filename}')">
  Download Image as <span style="text-transform:uppercase;">{format}</span>
</button>
"""

# store id of current plot
download_html += """\
<script>
  var current_divid = "{plot_id}";
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

# ----------------------------------------------------------------------

# hide all draggable elements except for those belonging to main axis
inject_html = """\
<script>
  (function(){
    let p = document.getElementById(current_divid);

    console.log("Hello, World!");
    console.log(p.data);
    console.log(p.layout);
    console.log(p.config);

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
  })();
</script>
"""

# remove Autoscale button because it dose not work well for layered ticks
inject_html += """\
<script>
  [...document.getElementById(current_divid).querySelectorAll("a.modebar-btn")]
    .forEach((item) =>
      {
        if (item.getAttribute("data-title") == "Autoscale")
        {
          item.parentNode.removeChild(item);
        }
      });
</script>
"""

# marge subplot titles
inject_html_ = """\
<script>
  (function(){
    let tags = [...document.getElementById(current_divid).querySelectorAll("g.infolayer > g")];
    let xtags = tags.filter((g) => g.className.baseVal.startsWith("g-x") && g.innerHTML);
    let xtexts = xtags.map((g) => g.querySelectorAll("text")[0].innerHTML);
    if (1 < xtags.length && xtexts.every((t) => t == xtexts[0]))
    {
      let xsum = 0.0;
      xtags.forEach((g, i) =>
        {
          xsum += parseFloat(
            g.querySelectorAll("text")[0].getAttribute("x"));
          if (0 < i) g.innerHTML = "";
        });
      xtags[0].querySelectorAll("text")[0].setAttribute("x", xsum/xtags.length);
    }
    let ytags = tags.filter((g) => g.className.baseVal.startsWith("g-y") && g.innerHTML);
    let ytexts = ytags.map((g) => g.querySelectorAll("text")[0].innerHTML);
    if (1 < ytags.length && ytexts.every((t) => t == ytexts[0]))
    {
      let ysum = 0.0;
      ytags.forEach((g, i) =>
        {
          ysum += parseFloat(
            g.querySelectorAll("text")[0].getAttribute("y"));
          if (0 < i) g.innerHTML = "";
        });
      let text_element = ytags[0].querySelectorAll("text")[0];
      let old_y = text_element.getAttribute("y");
      let old_transform = text_element.getAttribute("transform");
      let new_y = (ysum/ytags.length).toString();
      let new_transform = old_transform.slice(0, old_transform.lastIndexOf(old_y))+new_y+")";
      text_element.setAttribute("y", new_y);
      text_element.setAttribute("transform", new_transform);
    }
  })();
</script>
"""

def postprocess_by_js():
  ipd.display(ipd.HTML(inject_html))
