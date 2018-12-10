from utility import Parameter, algorithm
import numpy as np

class PatternSearch():
    def __init__(self):
        ''' Define default parameters '''
        self.name = 'PatternSearch'
        self.params = {}
        self.params['Step size'] = Parameter(name= 'Step size',
                                            value = 0.1,
                                            min = 0.001,
                                            max = 0.1,
                                            description = 'Initial step size')
        self.params['Samples'] = Parameter(name= 'Samples',
                                            value = 3,
                                            min = 1,
                                            max = 10,
                                            description = 'Initial samples per point')
        self.params['Tolerance'] = Parameter(name= 'Tolerance',
                                            value = 0.01,
                                            min = 0.001,
                                            max = 0.1,
                                            description = 'Convergence criterion')

    @algorithm
    def run(self, state):
        X, bounds = self.sampler.prepare(state)
        delta = self.params['Step size'].value
        N = int(self.params['Samples'].value)

        while delta > self.params['Tolerance'].value:

            ''' Form all search steps '''
            steps = []
            for i in range(len(X)):
                step = np.zeros(len(X))
                step[i] = delta
                steps.append(step.copy())
                step[i] = -delta
                steps.append(step.copy())

            ''' Sample cost function for all steps '''
            updated = False
            for i in range(len(X)):
                step = np.zeros(len(X))
                step[i] = delta
                ''' take steps in either direction'''
                f_X = []
                f_p = []
                f_n = []
                for n in range(N):
                    f_X.append(self.sampler._cost(X))
                    f_p.append(self.sampler._cost(X+step))
                    f_n.append(self.sampler._cost(X-step))

                z_p = (np.mean(f_X)-np.mean(f_p))/np.sqrt(np.std(f_X)**2/N+np.std(f_p)**2/N)
                z_n = (np.mean(f_X)-np.mean(f_n))/np.sqrt(np.std(f_X)**2/N+np.std(f_n)**2/N)

                significance_level = 1
                if z_p > significance_level/(2*len(X)):
                    X = X+step
                    updated = True
                elif z_n > significance_level/(2*len(X)):
                    X = X-step
                    updated = True
                else:
                    ''' measure contracted cost '''
                    f_p = []
                    f_n = []
                    for n in range(N):
                        f_p.append(self.sampler._cost(X+step/2))
                        f_n.append(self.sampler._cost(X-step/2))

                    z_p = (np.mean(f_X)-np.mean(f_p))/np.sqrt(np.std(f_X)**2/N+np.std(f_p)**2/N)
                    z_n = (np.mean(f_X)-np.mean(f_n))/np.sqrt(np.std(f_X)**2/N+np.std(f_n)**2/N)

                    if z_p > significance_level/(2*len(X)):
                        X = X+step/2
                        delta /= 2
                        updated = True
                    elif z_n > significance_level/(2*len(X)):
                        X = X-step/2
                        delta /= 2
                        updated = True
                    else:
                        N *= 2
            if not updated:
                delta /= 2

    def set_params(self, params):
        for p in params:
            self.params[p].value = params[p]
