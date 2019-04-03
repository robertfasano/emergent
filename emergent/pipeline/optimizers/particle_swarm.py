from emergent.utilities.containers import Parameter
import numpy as np
import itertools
from emergent.pipeline import Block

class ParticleSwarm(Block):
    def __init__(self, params={}):
        super().__init__()
        self.params = {}
        self.params['Steps'] = Parameter(name= 'Steps', type=int, value=10)
        self.params['Particles'] = Parameter(name= 'Particles', type=int, value=10)
        self.params['Velocity scale'] = Parameter(name= 'Initial velocity scale', value=1)
        self.params['Inertia'] = Parameter(name= 'Inertia', value=1)
        self.params['Cognitive acceleration'] = Parameter(name= 'Cognitive acceleration', value=0.1)
        self.params['Social acceleration'] = Parameter(name= 'Social acceleration', value=0.1)

        for p in params:
            self.params[p].value = params[p]

    def run(self, points, costs, bounds=None):
        ''' Differential evolution algorithm from scipy.optimize. '''
        particles = self.params['Particles'].value
        dim = points.shape[1]
        if bounds is None:
            bounds = np.array(list(itertools.repeat((0, 1), dim)))
        pos = np.empty((particles, dim))
        vel = np.empty((particles, dim))
        swarm_best_point = [0,0]
        swarm_best_cost = 999
        for i in range(points.shape[1]):
            pos[:,i] =  np.random.uniform(bounds[i][0], bounds[i][1], size=particles)
            v = bounds[i][1] - bounds[i][0]
            vel[:,i] =  np.random.uniform(-v, v, size=particles)
        vel *= self.params['Velocity scale'].value
        best_point = pos.copy()
        best_cost = np.empty(particles)
        for i in range(particles):
            points = np.append(points, np.atleast_2d(pos[i,:]), axis=0)
            costs = np.append(costs, self.source.measure(points[-1]))
            best_cost[i] = costs[-1]
            if costs[-1] < swarm_best_cost:
                swarm_best_point = points[-1]
                swarm_best_cost = costs[-1]

        for s in range(self.params['Steps'].value):
            for i in range(particles):
                rp = np.random.uniform(size=dim)
                rg = np.random.uniform(size=dim)
                vel[i, :] = self.params['Inertia'].value*vel[i, :]
                vel[i, :] += self.params['Cognitive acceleration'].value*rp*(best_point[i, :]-pos[i, :])
                vel[i, :] += self.params['Social acceleration'].value*rg*(swarm_best_point[:]-pos[i, :])
                pos[i, :] += vel[i, :]
                points = np.append(points, np.atleast_2d(pos[i, :]), axis=0)
                costs = np.append(costs, self.source.measure(points[-1]))
                if costs[-1] < best_cost[i]:
                    best_point[i,:] = points[-1]
                    best_cost[i] = costs[-1]
                    if costs[-1] < swarm_best_cost:
                        swarm_best_point = points[-1]
                        swarm_best_cost = costs[-1]

        points = np.append(points, np.atleast_2d(swarm_best_point), axis=0)
        costs = np.append(costs, self.source.measure(points[-1]))

        return points, costs
