from emergent.archetypes.node import Control

class TemplateControl(Control):
    def __init__(self, name, parent = None, path='.'):
        super().__init__(name, parent = parent, path=path)

    @experiment
    def measure_cost(self, state):
        ''' Moves to the target state and measures something. '''
        self.actuate(state)
        cost = do_something()    # add your own measurement function here
        return cost
