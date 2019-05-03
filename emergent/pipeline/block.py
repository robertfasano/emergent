import matplotlib.pyplot as plt
import time
import numpy as np

class Block():
    def __init__(self, state=None, bounds=None, cost=None, substate=None):
        self.pipeline = None

        if state is not None and bounds is not None and cost is not None:
            from emergent.pipeline import Pipeline
            self.pipeline = Pipeline(state, bounds, cost, substate=substate)
            self.pipeline.add(self)
            self.pipeline.run()

    def _run(self, points, costs, bounds=None):
        self.start_index = len(points)
        points, costs = self.run(points, costs, bounds)
        self.end_index = len(points)

        return points, costs

    def tune(self, parameter, bounds, steps=20, mode='cumulative'):
        ''' Args:
                parameter (str): the parameter to optimize
                bounds (tuple): optimization range
                mode (str): 'iterations': optimize the number of iterations for convergence
                            'result': optimize the final result
                            'improvement': optimize the improvement per iteration
        '''
        from emergent.pipeline import Pipeline

        meta_points = np.logspace(np.log10(bounds[0]),
                                  np.log10(bounds[1]),
                                  steps)
        meta_costs = []
        for point in meta_points:
            pipe = Pipeline(self.pipeline.state,
                            self.pipeline.scaler.limits,
                            self.pipeline.experiment,
                            verbose=False)
            self.params[parameter].value = point
            pipe.add(self)
            points, costs = pipe.run()
            if mode == 'iterations':
                meta_costs.append(len(points))
            elif mode == 'improvement':
                meta_costs.append(-(costs[-1]-costs[0])/len(points))
            elif mode == 'result':
                meta_costs.append(-(costs[-1]-costs[0]))
            elif mode == 'cumulative':
                meta_costs.append(np.sum(costs))

        plt.plot(meta_points, meta_costs)
        plt.xlabel(parameter)
        labels = {'iterations': 'Iterations for convergence',
                  'improvement': 'Improvement per iteration',
                  'result': 'Final result',
                  'cumulative': 'Cumulative cost'}
        plt.ylabel(labels[mode])
        if bounds[1]/bounds[0] > 100:
            plt.xscale('log')
        plt.show()

    def plot(self):
        self.pipeline.plot()
