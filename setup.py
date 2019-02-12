import os

from setuptools import setup, find_packages

version_ns = {}
with open(os.path.join("tk_plot_utils", "_version.py")) as f:
  exec(f.read(), {}, version_ns)

setup(
  name="tk_plot_utils",
  version=version_ns["__version__"],
  description="Personal functions to use Python's plotting libraries more easily",
  author="Takayuki Kobayashi",
  author_email="iris.takayuki@gmail.com",
  url="https://github.com/irisTa56/tk_plot_utils.git",
  packages=find_packages())
