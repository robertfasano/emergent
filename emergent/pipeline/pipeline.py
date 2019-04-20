import numpy as np
import importlib
import inspect
import matplotlib.pyplot as plt
import time
import json
from emergent.pipeline import BasePipeline, Scaler

import logging as log
log.basicConfig(level=log.INFO)

class Pipeline(BasePipeline):
    def __init__(self, state, bounds, experiment, params=None, substate=None, verbose=True):
        super().__init__()
        self.verbose = verbose
        self.experiment = experiment
        self.params = params
        self.state = state
        self.substate = substate
        if substate is None:
            self.substate = self.state
        self.scaler = Scaler(self.substate, bounds)

        self._points = np.atleast_2d(self.scaler.state2array(self.scaler.normalize(self.substate)))     # normalized points
        self.costs = np.array([self.measure(self.substate, norm=False)])
        self.points = self.unnormalize(self._points)
        self.bounds = []
        for d in range(self.points.shape[1]):
            self.bounds.append((0,1))

    def measure(self, state, norm=True):
        ''' Converts the array back to the form of d,
            unnormalizes it, and returns cost evaluated on the result.
            Args:
                norm (bool): whether the passed state is normalized '''
        if type(state) is np.ndarray:
            norm_target = self.scaler.array2state(state)
        else:
            norm_target = state
        if norm:
            target = self.scaler.unnormalize(norm_target)
        else:
            target = norm_target
        if self.params is None:
            return self.experiment(self.fill(target))
        else:
            return self.experiment(self.fill(target), self.params)

    def fill(self, substate):
        d = {}
        for key in self.state:
            if key in substate:
                d[key] = substate[key]
            else:
                d[key] = self.state[key]
        return d
    # def add_blocks(self, block_list):
    #     ''' Designed for compatibility with the PipelineLayout GUI element.
    #         Takes a list of dictionaries, each specifying a block and its params,
    #         and adds them. '''
    #     module = importlib.import_module('emergent.pipeline')
    #     for block in block_list:
    #         inst = getattr(module, block['block'])(params=block['params'])
    #         self.add(inst)

    def get_physical_bounds(self):
        min_state = self.scaler.array2state(np.zeros(self._points.shape[1]))
        max_state = self.scaler.array2state(np.ones(self._points.shape[1]))

        min = self.scaler.state2array(self.scaler.unnormalize(min_state))
        max = self.scaler.state2array(self.scaler.unnormalize(max_state))

        return [(min[i],max[i]) for i in range(self._points.shape[1])]

    def run(self):
        self.start_indices = []
        self.end_indices = []
        start_time = time.time()
        for block in self.blocks:
            self.start_indices.append(len(self.points))
            self._points, self.costs = block.run(self._points, self.costs, self.bounds)
            self.points = self.unnormalize(self._points)
            self.end_indices.append(len(self.points))

        end_time = time.time()
        self.duration = end_time - start_time
        if self.verbose:
            log.info('Optimization complete!')
            log.info('Time: %.0fs'%self.duration)
            log.info('Evaluations: %i'%len(self.points))
            log.info('Initial cost: %f'%self.costs[0])
            log.info('Final cost: %f'%self.costs[-1])

            percent_improvement = (self.costs[-1]-self.costs[0])/self.costs[0]*100
            log.info('Improvement: %.1f%%'%percent_improvement)

        return self.points, self.costs

    def unnormalize(self, points):
        dim = points.shape[1]
        _points = points.copy()
        bounds = self.get_physical_bounds()
        for d in range(dim):
            min = bounds[d][0]
            max = bounds[d][1]
            _points[:, d] = min + points[:, d] *(max-min)
        return _points


    def save(self, path, filename, pipeline=None):
        import os
        if pipeline is None:
            pipeline = self.to_json()
        if not os.path.exists(path):
            os.makedirs(path)
        try:
            with open(path+'/'+filename, 'r') as file:
                d = json.load(file)
        except FileNotFoundError:
            d = {}
        d['pipeline'] = pipeline
        with open(path+'/'+filename, 'w') as file:
            json.dump(d, file, indent=2)

    def load(self, path, filename):
        self.blocks = []
        with open(path+'%s'%filename, 'r') as file:
            d = json.load(file)
        self.from_json(d['pipeline'])
        return d['pipeline']
