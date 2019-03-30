import matplotlib.pyplot as plt

class Block():
    def __init__(self):
        self.pipeline, self.source = (None, None)

    def connect(self, pipeline):
        self.pipeline = pipeline
        self.source = pipeline.source

    def _run(self, points, costs, bounds=None):
        start_index = len(points)
        points, costs = self.run(points, costs, bounds)
        self.history_points = points[start_index::]
        self.history_costs = costs[start_index::]

        return points, costs

    def plot(self):
        if len(self.history_points) == 0:
            return
        plt.plot(self.history_costs, '.')
        plt.xlabel('Evalutions')
        plt.ylabel('Result')
        plt.show()
