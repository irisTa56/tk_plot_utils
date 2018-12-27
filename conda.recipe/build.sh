#!/bin/bash

sed -i -e "s/div//g" ./tk_plot_utils/_version.py

${PYTHON} setup.py install
