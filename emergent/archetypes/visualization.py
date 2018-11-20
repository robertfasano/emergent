import matplotlib.pyplot as plt
import threading
import logging as log
from scipy.interpolate import griddata
import numpy as np
import pandas as pd
from matplotlib.ticker import NullFormatter
import matplotlib.gridspec as gridspec


def plot_1D(points, costs, cost_name = 'Cost', normalized_cost = False, limits = None,
            save = False, ax = None):
    if threading.current_thread() is not threading.main_thread():
        log.warn('Cannot create matplotlib plot in thread.')
        return

    if ax is None:
        plt.figure()
        ax = plt.gca()

    points = points.copy()
    ordinate_index = 0
    abscissa_index = 1
    if limits is not None:
        name = list(limits.keys())[0]
        points = limits[name]['min'] + points*(limits[name]['max']-limits[name]['min'])
    ax.plot(points, costs, '.')
    if limits is not None and ax is None:
        plt.xlabel(name)
        plt.ylabel(cost_name)

    return ax

def plot_2D(points, costs, normalized_cost = False, limits = None,
            save = False, color_map='viridis_r', ax = None):
    ''' Interpolates and plots a cost function sampled at an array of points. '''
    if threading.current_thread() is not threading.main_thread():
        log.warn('Cannot create matplotlib plot in thread.')
        return

    points = points.copy()
    ordinate_index = 0
    abscissa_index = 1
    if limits is not None:
        names = list(limits.keys())
        for i in [0,1]:
            points[:,i] = limits[names[i]]['min'] + points[:,i]*(limits[names[i]]['max']-limits[names[i]]['min'])
    ordinate_mesh, abscissa_mesh = np.meshgrid(points[:,ordinate_index], points[:, abscissa_index])
    # normalized_costs = -1*(costs - np.min(costs))/(np.max(costs)-np.min(costs)) + 1
    # if normalized_cost:
        # cost_grid = griddata(points[:,[ordinate_index, abscissa_index]], normalized_costs, (ordinate_mesh,abscissa_mesh))
    # else:
    cost_grid = griddata(points[:,[ordinate_index, abscissa_index]], costs, (ordinate_mesh,abscissa_mesh))
    # plot = ax.pcolormesh(ordinate_mesh, abscissa_mesh, cost_grid, cmap=color_map)
    i = int(len(points)/2)
    best_point = points[np.argmin(costs)]
    ix = int(best_point[0]*cost_grid.shape[0])
    iy = int(best_point[1]*cost_grid.shape[1])

    xi = ordinate_mesh[ix,:]
    yi = abscissa_mesh[:,iy]
    zix = cost_grid[iy,:]
    ziy = cost_grid[:,ix]

    if limits is not None:
        plt.xlabel(names[0])
        plt.ylabel(names[1])

    ''' Plot cross sections around the best point '''
    fig = plt.figure(figsize=(10,8))
    gs = gridspec.GridSpec(10, 10)

    ax0 = plt.subplot(gs[0:8, 0:8])
    axx = plt.subplot(gs[8:10, 0:8])
    axy = plt.subplot(gs[0:8, 8:10])

    plot = ax0.pcolormesh(ordinate_mesh, abscissa_mesh, cost_grid, cmap=color_map)
    # plt.colorbar(plot, ax = ax0)

    axx.plot(xi, zix, '.')
    axy.plot(ziy, yi, '.')

    nullfmt = NullFormatter()
    ax0.xaxis.set_major_formatter(nullfmt)
    ax0.yaxis.set_major_formatter(nullfmt)
    axy.yaxis.tick_right()
    # axx.xaxis.set_major_formatter(nullfmt)
    # axx.yaxis.set_major_formatter(nullfmt)
    # axy.xaxis.set_major_formatter(nullfmt)
    # axy.yaxis.set_major_formatter(nullfmt)

    return ax
