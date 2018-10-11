import matplotlib.pyplot as plt
import threading
import logging as log
from scipy.interpolate import griddata
import numpy as np
import pandas as pd



def plot_1D(points, costs, normalized_cost = False, limits = None,
            save = False):
    if threading.current_thread() is not threading.main_thread():
        log.warn('Cannot create matplotlib plot in thread.')
        return

    plt.figure()
    points = points.copy()
    ordinate_index = 0
    abscissa_index = 1
    if limits is not None:
        name = list(limits.keys())[0]
        points = limits[name]['min'] + points*(limits[name]['max']-limits[name]['min'])
    plt.plot(points, costs)
    if save:
        plt.savefig(self.parent.data_path + str(time.time()) + '.png')
    ax = plt.gca()
    if limits is not None:
        plt.xlabel(name)
        plt.ylabel('Cost')

    return ax

def plot_2D(points, costs, normalized_cost = False, limits = None,
            save = False, color_map='viridis_r'):
    ''' Interpolates and plots a cost function sampled at an array of points. '''
    if threading.current_thread() is not threading.main_thread():
        log.warn('Cannot create matplotlib plot in thread.')
        return
    plt.figure()
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
    plot = plt.pcolormesh(ordinate_mesh, abscissa_mesh, cost_grid, cmap=color_map)
    plt.colorbar(plot)
    if save:
        plt.savefig(self.parent.data_path + str(time.time()) + '.png')
    ax = plt.gca()
    if limits is not None:
        plt.xlabel(names[0])
        plt.ylabel(names[1])

    return ax
