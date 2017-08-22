import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def mysetting(font_family="Arial",
              font_size=18,
              lines_markersize=5.0,
              axes_linewidth=1.0,
              legend_frameon=True,
              legend_labelspacing=0.3,
              legend_handletextpad=0.2,
              figure_subplot_left=0.15,
              figure_subplot_right=0.95,
              figure_subplot_bottom=0.15,
              figure_subplot_top=0.95,
              xtick_top=True,
              xtick_bottom=True,
              xtick_minor_visible=True,
              xtick_direction='in',
              xtick_major_size=5.0,
              xtick_minor_size=3.0,
              xtick_major_width=1.0,
              xtick_minor_width=1.0,
              ytick_left=True,
              ytick_right=True,
              ytick_minor_visible=True,
              ytick_direction='in',
              ytick_major_size=5.0,
              ytick_minor_size=3.0,
              ytick_major_width=1.0,
              ytick_minor_width=1.0):
    plt.rcParams['font.family'] = font_family
    plt.rcParams['font.size'] = font_size
    plt.rcParams['lines.markersize'] = lines_markersize
    plt.rcParams['axes.linewidth'] = axes_linewidth
    plt.rcParams['legend.frameon'] = legend_frameon
    plt.rcParams['legend.labelspacing'] = legend_labelspacing
    plt.rcParams['legend.handletextpad'] = legend_handletextpad
    plt.rcParams['figure.subplot.left'] = figure_subplot_left
    plt.rcParams['figure.subplot.right'] = figure_subplot_right
    plt.rcParams['figure.subplot.bottom'] = figure_subplot_bottom
    plt.rcParams['figure.subplot.top'] = figure_subplot_top
    plt.rcParams['xtick.top'] = xtick_top
    plt.rcParams['xtick.bottom'] = xtick_bottom
    plt.rcParams['xtick.minor.visible'] = xtick_minor_visible
    plt.rcParams['xtick.direction'] = xtick_direction
    plt.rcParams['xtick.major.size'] = xtick_major_size
    plt.rcParams['xtick.minor.size'] = xtick_minor_size
    plt.rcParams['xtick.major.width'] = xtick_major_width
    plt.rcParams['xtick.minor.width'] = xtick_minor_width
    plt.rcParams['ytick.left'] = ytick_left
    plt.rcParams['ytick.right'] = ytick_right
    plt.rcParams['ytick.minor.visible'] = ytick_minor_visible
    plt.rcParams['ytick.direction'] = ytick_direction
    plt.rcParams['ytick.major.size'] = ytick_major_size
    plt.rcParams['ytick.minor.size'] = ytick_minor_size
    plt.rcParams['ytick.major.width'] = ytick_major_width
    plt.rcParams['ytick.minor.width'] = ytick_minor_width

def read_fromPlainText(FileNames, HeaderNames, MinRow, MaxRow,
                       ColumnIndex_X, ColumnIndex_Y,
                       Rescale_X=1.0, Rescale_Y=1.0):
    # prepare
    if type(ColumnIndex_X) != list:
        ColumnIndex_X = [ColumnIndex_X] * len(FileNames)
    if type(ColumnIndex_Y) != list:
        ColumnIndex_Y = [ColumnIndex_Y] * len(FileNames)
    if type(Rescale_X) != list:
        Rescale_X = [Rescale_X] * len(FileNames)
    if type(Rescale_Y) != list:
        Rescale_Y = [Rescale_Y] * len(FileNames)
    # read data as pandas DataFrame
    data = []
    for filename in FileNames:
        data.append(
            pd.read_csv(
                filename,
                delim_whitespace=True,
                names=HeaderNames,
                skiprows=MinRow-1,
                nrows=MaxRow-MinRow+1
            )
        )
    # data for x-axis
    xs = []
    for (data_, cix_, rx_) in zip(data, ColumnIndex_X, Rescale_X):
        xs.append(np.array(data_.values).T[cix_]*rx_)
    # data for y-axis
    ys = []
    for (data_, ciy_, ry_) in zip(data, ColumnIndex_Y, Rescale_Y):
        ys.append(np.array(data_.values).T[ciy_]*ry_)
    # return
    return [xs, ys]

def plot_simple(DataX, DataY, Colors, Lines, MinX, MaxX, MinY, MaxY,
                LineWidth=1,  ScaleX="linear", ScaleY="linear",
                Labels=[], LabelX="x-axis", LabelY="y-axis",
                Width=5.0, Height=4.5, PlotName="myplot", LegendNumColumns=1):
    if len(Labels) == 0:
        Labels = range(len(PlotStyles))
    plt.figure(figsize=(Width,Height))
    plt.xlim(MinX, MaxX)
    plt.ylim(MinY, MaxY)
    for (x, y, label, color, line) in zip(DataX, DataY, Labels, Colors, Lines):
        plt.plot(
            x, y, color=color, linestyle=line, linewidth=LineWidth, label=label
        )
    plt.legend(loc='best', ncol=LegendNumColumns)
    if ScaleX == "log":
        plt.xscale(ScaleX)
    if ScaleY == "log":
        plt.yscale(ScaleY)
    plt.xlabel(LabelX)
    plt.ylabel(LabelY)
    plt.savefig(PlotName+".pdf")
    plt.savefig(PlotName+".svg")
