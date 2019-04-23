from emergent.pipeline import Block

class Measure(Block):
    ''' Makes a measurement of the Pipeline's experiment. '''
    def __init__(self, params={}):
        super().__init__()

    def run(self, points, costs, bounds=None):
        ''' Retrain the model on passed data'''
        costs = np.append(costs, self.pipeline.measure(points[-1]))
        points = np.append(points, np.atleast_2d(points[-1]), axis=0)
        return points, costs
