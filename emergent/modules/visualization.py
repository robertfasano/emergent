import matplotlib.pyplot as plt
import threading
import logging as log
from scipy.interpolate import griddata
import numpy as np
import pandas as pd
from matplotlib.ticker import NullFormatter
import matplotlib.gridspec as gridspec
plt.ioff()

def plot_1D(points, costs, cost_name = 'Cost', normalized_cost = False, limits = None,
            save = False, ax = None, xlabel = None, ylabel = None, errors = None):
    if threading.current_thread() is not threading.main_thread():
        log.warn('Cannot create matplotlib plot in thread.')
        return
    passed_ax = ax
    fig = None
    if ax is None:
        fig = plt.figure()
        ax = plt.gca()

    points = points.copy()
    ordinate_index = 0
    abscissa_index = 1
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
    return ax, fig

def plot_2D(points, costs, normalized_cost = False, limits = None,
            save = False, color_map='viridis_r', ax = None):
    ''' Interpolates and plots a cost function sampled at an array of points. '''
    if threading.current_thread() is not threading.main_thread():
        log.warn('Cannot create matplotlib plot in thread.')
        return

    costs = costs.copy()[::-1]
    points = points.copy()[::-1]        # ignore last point where we return to max, since this messes up the interpolation
    norm_points = points.copy()[::-1]
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
    i = int(len(points)/2)
    best_norm_point = norm_points[np.argmax(costs)]
    best_point = points[np.argmax(costs)]

    ix = int(best_norm_point[0]*cost_grid.shape[0])
    iy = int(best_norm_point[1]*cost_grid.shape[1])

    if ix == cost_grid.shape[0]:
        ix -= 1
    if iy == cost_grid.shape[1]:
        iy -= 1
    xi = ordinate_mesh[ix,:]
    yi = abscissa_mesh[:,iy]
    zix = cost_grid[iy,:]
    ziy = cost_grid[:,ix]


    ''' Plot cross sections around the best point '''
    fig = plt.figure(figsize=(10,8))
    gs = gridspec.GridSpec(10, 10)

    ax0 = plt.subplot(gs[0:8, 0:8])
    axx = plt.subplot(gs[8:10, 0:8])
    axy = plt.subplot(gs[0:8, 8:10])
    # ax0.scatter(points[:,0], points[:,1])
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

    ''' Plot crosshairs through best point '''
    xline = np.linspace(points[:,0].min(), points[:,0].max(),100)
    xliney = best_point[1]*np.ones(len(xline))
    ax0.plot(xline, xliney, 'k')
    yline = np.linspace(points[:,1].min(), points[:,1].max(),100)
    ylinex = best_point[0]*np.ones(len(yline))
    ax0.plot(ylinex, yline, 'k')
    ax0.scatter(np.array(best_point[0]), np.array(best_point[1]), marker='o', c='k')


    if limits is not None:
        axx.set_xlabel(names[0])
        axy.set_ylabel(names[1])
        axy.yaxis.set_label_position("right")

    plt.tight_layout(pad=0.5)
    return fig
