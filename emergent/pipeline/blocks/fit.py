from emergent.pipeline import Block

class Fit(Block):
    ''' Should be attached to a Model block rather than the primary pipeline. Allows the model
        to be retrained on current data wherever this block is inserted. '''
    def __init__(self):
        super().__init__()

    def run(self, points, costs, bounds=None):
        ''' Retrain the model on passed data'''
        self.pipeline.fit(points, costs)
        return points, costs
