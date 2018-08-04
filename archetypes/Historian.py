import numpy as np
import pandas as pd
import json


class Historian():
    ''' The Historian class attaches to a Control node to provide a history of
    explored states. '''
    def __init__(self, parent):
        self.parent = parent
        self.state_path = self.parent.state_path + self.parent.name + '.txt'
        self.settings_path = self.parent.settings_path + self.parent.name + '.txt'

    def load(self):
        ''' Loads all historical state data and returns a dataframe. '''
        with open(self.state_path, 'r') as file:
            data = file.readlines()

        t = []
        states = []

        state = json.loads(data[0].split('\t')[1])
        df = pd.DataFrame(index=[], columns=list(state.keys()))
        for i in range(len(data)):
            t = data[i].split('\t')[0]
            state = json.loads(data[i].split('\t')[1])
            temp = pd.DataFrame(index=[t], columns=list(state.keys()))
            for key in state.keys():
                temp[key] = state[key]
            df = df.append(temp)

        return df

    def clear(self):
        ''' Deletes historical state data up to the last point. '''
        for p in [self.state_path, self.settings_path]:
            with open(p, 'r') as file:
                line = file.readlines()[-1]
            with open(p, 'w') as file:
                file.write(line)
