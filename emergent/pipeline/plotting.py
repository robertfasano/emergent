''' The plotting module allows 1D or 2D plots to be created and return a figure
    and axis, such that widgets can generate plots with very little of their own code. '''
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import numpy as np
import pandas as pd
from matplotlib.ticker import NullFormatter
import matplotlib.gridspec as gridspec
from mpl_toolkits import mplot3d
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QComboBox
plt.ioff()

def plot_1D(points, costs, cost_name = 'Cost', normalized_cost = False, limits = None,
            save = False, ax = None, xlabel = None, ylabel = None, errors = None, yscale='linear'):
    passed_ax = ax
    fig = None
    if ax is None:
        fig = plt.figure()
        ax = plt.gca()

    points = points.copy()
    if limits is not None:
        name = list(limits.keys())[0]
        points = limits[name]['min'] + points*(limits[name]['max']-limits[name]['min'])
    if errors is None:
        ax.plot(points, costs, '.')
    else:
        ax.errorbar(points, costs, yerr=errors, fmt='.')
    if limits is not None and passed_ax is None:
        plt.xlabel(name)
        plt.ylabel(cost_name)
    if xlabel is not None:
        plt.xlabel(xlabel)
    if ylabel is not None:
        plt.ylabel(ylabel)
    plt.tight_layout(pad=4)
    plt.yscale(yscale)
    return ax, fig

def plot_2D(points, costs, color_map='viridis_r', ax = None, mode='cross-section'):
    ''' Interpolates and plots a cost function sampled at an array of points. It's expected
        that the passed data fills the bounds of the space. '''
    costs = costs.copy()
    points = points.copy()        # ignore last point where we return to max, since this messes up the interpolation
    dim = points.shape[1]

    ordinate_mesh, abscissa_mesh = np.meshgrid(points[:,0], points[:, 1])

    cost_grid = griddata(points[:,[0, 1]], costs, (ordinate_mesh,abscissa_mesh))


    fig = plt.figure(figsize=(10,8))
    gs = gridspec.GridSpec(10, 10)

    if mode == 'cross-section':
        ''' Plot cross sections around the best point '''
        i = int(len(points)/2)
        best_point = points[np.argmin(costs)]
        best_point_norm = best_point.copy()
        for d in range(2):
            min = points[:, d].min()
            max = points[:, d].max()
            best_point_norm[d] = (best_point_norm[d]-min)/(max-min)

        ix = int(best_point_norm[0]*cost_grid.shape[0])
        iy = int(best_point_norm[1]*cost_grid.shape[1])
        if ix == cost_grid.shape[0]:
            ix -= 1
        if iy == cost_grid.shape[1]:
            iy -= 1
        xi = ordinate_mesh[ix,:]
        yi = abscissa_mesh[:,iy]
        zix = cost_grid[iy,:]
        ziy = cost_grid[:,ix]

        ax0 = plt.subplot(gs[0:8, 0:8])
        axx = plt.subplot(gs[8:10, 0:8])
        axy = plt.subplot(gs[0:8, 8:10])
        plot = ax0.pcolormesh(ordinate_mesh, abscissa_mesh, cost_grid, cmap=color_map)


        axx.plot(xi, zix, '.')
        axy.plot(ziy, yi, '.')


        axy.yaxis.tick_right()


        ''' Plot crosshairs through best point '''
        xline = np.linspace(points[:,0].min(), points[:,0].max(),100)
        xliney = best_point[1]*np.ones(len(xline))
        ax0.plot(xline, xliney, 'k')
        yline = np.linspace(points[:,1].min(), points[:,1].max(),100)
        ylinex = best_point[0]*np.ones(len(yline))
        ax0.plot(ylinex, yline, 'k')
        ax0.scatter(np.array(best_point[0]), np.array(best_point[1]), marker='o', c='k')
    elif mode == 'surface':
        ax0 = plt.axes(projection='3d')
        plot = ax0.plot_surface(ordinate_mesh, abscissa_mesh, cost_grid, rstride=1, cstride=1,
                    cmap='viridis', edgecolor='none')

    nullfmt = NullFormatter()
    ax0.xaxis.set_major_formatter(nullfmt)
    ax0.yaxis.set_major_formatter(nullfmt)

    plt.tight_layout(pad=0.5)
    return fig

class PlotWindow(QWidget):
    def __init__(self, data):
        super().__init__()
        self.plot_tabs(data)
        self.setWindowTitle('Pipeline results')
        self.show()

    def widget(self, y, x=None, labels={'left': '', 'bottom': ''}):
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        pw = pg.PlotWidget(pen=None, labels=labels)

        pw.plot(x=x, y=y, symbol='o', symbolSize=5, pen=None)
        return pw

    def plot_tabs(self, data):
        import numpy as np
        layout = QVBoxLayout()
        self.setLayout(layout)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        ''' Optimization tab '''
        plot_data = data['Optimization']
        tab_widget = self.widget(x=plot_data['x'], y=plot_data['y'], labels=plot_data['labels'])
        tabs.addTab(tab_widget, 'Optimization')

        ''' Cost vs parameter tab '''
        tab_widget = QWidget()
        self.tab_layout = QVBoxLayout()
        tab_widget.setLayout(self.tab_layout)
        tabs.addTab(tab_widget, '1D')

        box = QComboBox()
        box.currentTextChanged.connect(self.plot_axis)
        pipe_data = data['Data']
        self.points = np.atleast_2d(data['Data']['points'])
        self.costs = np.array(data['Data']['costs'])
        self.axis_widget = self.widget(x=self.points[:, 0], y=self.costs)

        self.tab_layout.addWidget(box)
        for item in range(self.points.shape[1]):
            box.addItem(str(item))
        self.tab_layout.addWidget(self.axis_widget)

    def plot_axis(self, axis):
        axis = int(axis)
        new_widget = self.widget(x=self.points[:, axis], y=self.costs, labels={'bottom': str(axis), 'left': 'Result'})
        self.tab_layout.replaceWidget(self.axis_widget, new_widget)
        self.axis_widget = new_widget
