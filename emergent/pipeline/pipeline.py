import numpy as np
import importlib
import inspect
import matplotlib.pyplot as plt
import logging as log
import time
import json
from emergent.pipeline.scaler_dev import Scaler_dev

class Pipeline:
    def __init__(self, experiment, params, state, bounds):
        self.experiment = experiment
        self.params = params
        self.state = state
        self.blocks = []

        self.scaler = Scaler_dev(state, bounds)


        self._points = np.atleast_2d(self.scaler.state2array(self.scaler.normalize(self.state)))     # normalized points
        self.costs = np.array([self.measure(self.state, norm=False)])
        self.points = self.unnormalize_dev(self._points)
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

        return self.experiment(target, self.params)


    def add(self, block):
        self.blocks.append(block)
        block.connect(self)

    def add_blocks(self, block_list):
        ''' Designed for compatibility with the PipelineLayout GUI element.
            Takes a list of dictionaries, each specifying a block and its params,
            and adds them. '''
        module = importlib.import_module('emergent.pipeline')
        for block in block_list:
            inst = getattr(module, block['block'])(params=block['params'])
            self.add(inst)

    def add_source(self, source):
        self.source = source
        self._points = np.atleast_2d(source.scaler.state2array(source.scaler.normalize(self.state)))     # normalized points
        self.costs = np.array([source.measure(self.state, norm=False)])
        self.points = self.unnormalize(self._points)

        self.bounds = []
        for d in range(self.points.shape[1]):
            self.bounds.append((0,1))

        for block in self.blocks:
            block.source = source

    def get_physical_bounds(self):
        min = self.source.scaler.unnormalize(np.array([0,0]), array=True)
        max = self.source.scaler.unnormalize(np.array([1,1]), array=True)

        return [(min[i],max[i]) for i in range(self._points.shape[1])]

    def get_physical_bounds_dev(self):
        min = self.scaler.unnormalize(np.array([0,0]), array=True)
        max = self.scaler.unnormalize(np.array([1,1]), array=True)

        return [(min[i],max[i]) for i in range(self._points.shape[1])]

    def run(self):
        self.start_indices = []
        self.end_indices = []
        start_time = time.time()
        for block in self.blocks:
            self.start_indices.append(len(self.points))
            self._points, self.costs = block.run(self._points, self.costs, self.bounds)
            self.points = self.unnormalize_dev(self._points)
            self.end_indices.append(len(self.points))

        end_time = time.time()
        self.duration = end_time - start_time
        log.info('Optimization complete!')
        log.info('Time: %.0fs'%self.duration)
        log.info('Evaluations: %i'%len(self.points))
        percent_improvement = (self.costs[-1]-self.costs[0])/self.costs[0]*100
        log.info('Improvement: %.1f%%'%percent_improvement)

        return self.points, self.costs

    def list_optimizers(self):
        module = importlib.import_module('emergent.pipeline.optimizers')
        names = []
        for a in dir(module):
            if '__' not in a:
                inst = getattr(module, a)
                if inspect.isclass(inst):
                    names.append(inst.__name__)
        return names

    def list_models(self):
        module = importlib.import_module('emergent.pipeline.models')
        names = []
        for a in dir(module):
            if '__' not in a:
                inst = getattr(module, a)
                if inspect.isclass(inst):
                    names.append(inst.__name__)
        return names

    def list_blocks(self):
        module = importlib.import_module('emergent.pipeline.blocks')
        names = []
        for a in dir(module):
            if '__' not in a:
                inst = getattr(module, a)
                if inspect.isclass(inst):
                    names.append(inst.__name__)
        return names

    def unnormalize(self, points):
        dim = points.shape[1]
        _points = points.copy()
        bounds = self.get_physical_bounds()
        for d in range(dim):
            min = bounds[d][0]
            max = bounds[d][1]
            _points[:, d] = min + points[:, d] *(max-min)
        return _points

    def unnormalize_dev(self, points):
        dim = points.shape[1]
        _points = points.copy()
        bounds = self.get_physical_bounds_dev()
        for d in range(dim):
            min = bounds[d][0]
            max = bounds[d][1]
            _points[:, d] = min + points[:, d] *(max-min)
        return _points
    # def plot(self):
    #     if len(self.points) == 0:
    #         return
    #     # widget(self.costs)
    #     plt.plot(self.costs, '.k')
    #     plt.plot(np.minimum.accumulate(self.costs), '--k')
    #
    #     plt.xlabel('Evalutions')
    #     plt.ylabel('Result')
    #     plt.show()

    # def plot(self):
    #     tabs = {}
    #
    #     tabs['Optimization'] = {'x': None, 'y': self.costs.tolist(), 'labels': {'bottom': 'Iterations', 'left': 'Result'}}
    #     tabs['Data'] = {'points': self.points.tolist(), 'costs': self.costs.tolist()}
    #     self.network.emit('plot', tabs)

    def get_json(self):
        blocks = []
        for block in self.blocks:
            params = {}
            for p in block.params:
                params[p] = block.params[p].value
            blocks.append({'block': block.__class__.__name__,
                           'params': params})
        return blocks

    # def save(self, name, pipeline=None):
    #     import os
    #     if pipeline is None:
    #         pipeline = self.get_json()
    #     path = self.network.path['pipelines']
    #     if not os.path.exists(path):
    #         os.makedirs(path)
    #
    #     with open(path+'%s.json'%name, 'w') as file:
    #         json.dump(pipeline, file)
    #
    # def load(self, name):
    #     path = self.network.path['pipelines']
    #     with open(path+'%s.json'%name, 'r') as file:
    #         self.add_blocks(json.load(file))
