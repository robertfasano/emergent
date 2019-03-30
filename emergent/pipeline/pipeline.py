import numpy as np
import importlib
import inspect
import matplotlib.pyplot as plt

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
        for block in self.blocks:
            self.points, self.costs = block._run(self.points, self.costs, self.bounds)
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
        plt.plot(self.costs, '.')
        plt.xlabel('Evalutions')
        plt.ylabel('Result')
        plt.show()
