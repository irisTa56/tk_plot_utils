<!--
   tk_plot_utils documentation master file, created by
   sphinx-quickstart on Mon Feb 11 09:33:27 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.
-->

# Welcome to tk_plot_utils's documentation!

```eval_rst
.. toctree::
   :maxdepth: 1
   :caption: Contents:
   :hidden:

   apis/modules
```

`tk_plot_utils` is an interface to [Plotly (plotly.py)](https://github.com/plotly/plotly.py), an interactive graphing library for Python. Plotly has many remarkable functionalities and is easy to use. However, I found some difficulties when using it. Plotly's default layouts of plot might be too casual for some purposes. In addition, it is difficult to download plot images in SVG format. Solving these problems is the main goal of this interface package.

## Prerequisites

* [plotly/plotly.py](https://github.com/plotly/plotly.py)

## Install

Conda.

```bash
conda install -c irista56 tk_plot_utils
```

Clone and install.

```bash
git clone https://github.com/irisTa56/tk_plot_utils.git
cd tk_plot_utils
python setup.py install
```

Download and install from this repository using pip.

```bash
pip install git+https://github.com/irisTa56/tk_plot_utils.git
```

## Example Notebooks

Google Chrome is recommended.

* [First Demo](https://nbviewer.jupyter.org/github/irisTa56/tk_plot_utils/blob/master/examples/first_demo.ipynb)
* [Single Scatter Plot](https://nbviewer.jupyter.org/github/irisTa56/tk_plot_utils/blob/master/examples/single_scatter_plot.ipynb)
* [Multiple Scatter Plot](https://nbviewer.jupyter.org/github/irisTa56/tk_plot_utils/blob/master/examples/multiple_scatter_plot.ipynb)
* [Heatmap Plot](https://nbviewer.jupyter.org/github/irisTa56/tk_plot_utils/blob/master/examples/heatmap_plot.ipynb)
* [Scatter Subplots](https://nbviewer.jupyter.org/github/irisTa56/tk_plot_utils/blob/master/examples/subplots_scatter.ipynb)
* [Scatter Subplots with Shared Axis](https://nbviewer.jupyter.org/github/irisTa56/tk_plot_utils/blob/master/examples/shared_axis_subplots_scatter.ipynb)
* [Heatmap Subplots](https://nbviewer.jupyter.org/github/irisTa56/tk_plot_utils/blob/master/examples/subplots_heatmap.ipynb)
* [Logarithmic-Scale Scatter Plot](https://nbviewer.jupyter.org/github/irisTa56/tk_plot_utils/blob/master/examples/log_scale_scatter.ipynb)

## Acknowledgement

This project would not be possible without the following great open-source projects.

* [plotly/plotly.py](https://github.com/plotly/plotly.py)
* [zenorocha/clipboard.js](https://github.com/zenorocha/clipboard.js)

## Indices and tables

* [Index](genindex)
* [Module Index](modindex)
* [Search](search)
