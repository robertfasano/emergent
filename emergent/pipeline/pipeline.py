import numpy as np
import importlib
import inspect
import matplotlib.pyplot as plt
import logging as log
import time

class Pipeline:
    def __init__(self, state, source):
        self.source = source
        self.points = np.atleast_2d(source.scaler.state2array(source.scaler.normalize(state)))
        self.costs = np.array([source.measure(state, norm=False)])

        self.bounds = []
        for d in range(self.points.shape[1]):
            self.bounds.append((0,1))

        self.blocks = []

    def add(self, block):
        self.blocks.append(block)
        block.connect(self)

    def run(self):
        self.start_indices = []
        self.end_indices = []
        start_time = time.time()
        for block in self.blocks:
            self.start_indices.append(len(self.points))
            self.points, self.costs = block.run(self.points, self.costs, self.bounds)
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

    def plot(self):
        if len(self.points) == 0:
            return
        plt.plot(self.costs, '.k')
        plt.plot(np.minimum.accumulate(self.costs), '--k')

        plt.xlabel('Evalutions')
        plt.ylabel('Result')
        plt.show()
