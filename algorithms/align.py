''' This script implements an Aligner class from which many devices inherit methods such as:
    persistent positioning, first light acquisition, and realtime optimization
'''
import numpy as np
import sys
import os
import json
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-2]))     

class Aligner():
    def __init__(self, filename):
        self.filename = filename
        self.position = np.array([])
        self.zero = np.array([])
        
    def load_position(self):
        ''' Recalls the last saved position to ensure that alignment is persistent
            across device restarts '''
        with open(self.filename, 'r') as file:
            self.parameters = json.load(file)
        self.position = self.parameters['position']
        
    def actuate(self, point):
        self.position = point

    def explore(self, span, steps, axes = None, plot = False):
        ''' An N-dimensional grid search routine '''
        position = self.position
        if axes != None:
            position = position[axes]
            
        ''' Generate search grid '''
        N = len(position)
        grid = []
        for n in range(N):
            space = np.linspace(position[n]-span/2, position[n]+span/2, steps)
            grid.append(space)
        grid = np.array(grid)
        points = np.transpose(np.meshgrid(*[grid[n] for n in range(N)])).reshape(-1,N)
        
        ''' Actuate search '''
        cost = []
        for point in points:
            self.actuate(point)
            cost.append(self.cost())
            
        ''' Plot result if desired '''
        if plot:
            if len(position) == 2 and axes == None:
                ordinate_index = 0
                abscissa_index = 1
            elif len(position) == 2:
                ordinate_index = axes[0]
                abscissa_index = axes[1]
            ordinate_mesh, abscissa_mesh = np.meshgrid(points[:,ordinate_index], points[:, abscissa_index])
            cost_grid = griddata(points[:,[ordinate_index, abscissa_index]], cost, (ordinate_mesh,abscissa_mesh))
            plot = plt.pcolormesh(ordinate_mesh, abscissa_mesh, cost_grid, cmap='gist_rainbow')
            plt.colorbar(plot)
            
            
        return points

    def cost(self):
        ''' A gaussian cost function in N dimensions. Overload in child classes with appropriate function '''
        cost = 1
        sigma = 1
        point = self.position
        for n in range(len(point)):
            cost *= np.exp(-point[n]**2/(2*sigma**2))
        return cost   
        
if __name__ == '__main__':
    a = Aligner(None)
    a.position = np.array([0,0, 20])
    c = a.explore(5,30, axes = [0,1], plot = True)


