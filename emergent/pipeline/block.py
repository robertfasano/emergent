import matplotlib.pyplot as plt
import time

class Block():
    def __init__(self):
        self.pipeline = None

    def _run(self, points, costs, bounds=None):
        self.start_index = len(points)
        points, costs = self.run(points, costs, bounds)
        self.end_index = len(points)

        return points, costs
