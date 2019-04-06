from abc import abstractmethod
from emergent.pipeline import BasePipeline
import numpy as np
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

class Model(BasePipeline):
    ''' The Model class inherits elements from both Pipeline and Block - it is a subpipeline
        which can consume data from the primary pipeline to fit a surface to observed data,
        numerically optimize the surface to inform future sampling choices, then make a physical
        measurement at the optimized point.

        '''
    def __init__(self):
        super().__init__()


    @abstractmethod
    def measure(self, X):
        ''' Returns the model's prediction of the cost surface at a point X. Should be reimplemented
            for each given model. '''
        return

    @abstractmethod
    def fit(self, points, costs):
        '''Trains the model on the passed data. Reimplement for a given model. '''
        return

    def run(self, points, costs, bounds=None):
        ''' Trains on the passed data, numerically optimizes the modeled response
            surface according to the added blocks, then makes a physical measurement
            at the modeled minimum. '''
        # _points = points.copy()
        # _costs = costs.copy()
        self.fit(points, costs)
        self.points = np.atleast_2d(points[-1].copy())
        self.costs = costs[-1].copy()
        for block in self.blocks:
            self.points, self.costs = block.run(self.points, self.costs)

        ## make physical measurement
        self.best_point = self.points[np.argmin(self.costs)]
        best_cost = np.array([self.pipeline.measure(self.best_point)])

        points = np.append(points, np.atleast_2d(self.best_point), axis=0)
        costs = np.append(costs, best_cost)
        return points, costs

    def plot(self, axis):
        ''' Plots a 1D cross-section through the minimum of the modeled surface. '''
        dim = self.best_point.shape[0]
        n_points = 100

        points = np.zeros((n_points, dim))
        for d in range(dim):
            points[:, d] = self.best_point[d]
        points[:, axis] = np.linspace(self.pipeline.bounds[axis][0],
                                      self.pipeline.bounds[axis][1],
                                      n_points)
        costs = self.predict(points)[0]
        win = pg.GraphicsWindow()
        win.setWindowTitle('Modeled surface')
        label = pg.LabelItem(justify = "right")
        label.setText('goo!')
        win.addItem(label)
        p = win.addPlot(row = 1, col = 0, labels={'bottom': 'Axis %i'%axis, 'left': 'Result'})

        def mouseMoved(evt):
            mousePoint = p.vb.mapSceneToView(evt[0])
            label.setText("x = %0.2f, y = %0.2f</span>" % (mousePoint.x(), mousePoint.y()))

        points = self.pipeline.unnormalize(points)
        x = points[:,axis]
        y = costs
        plot = p.plot(x=x, y=y, symbol='o', symbolSize=7, pen=None)

        proxy = pg.SignalProxy(p.scene().sigMouseMoved, rateLimit=60, slot=mouseMoved)

        return win, proxy
