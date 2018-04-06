import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

def uptime(filename, choice):
    boolfile = filename.replace('log', 'bool')
    try:
        data = pd.read_csv(boolfile,delimiter='\t',index_col = 0)
    except:
        data=pd.DataFrame(index=[]) 
        print('ERROR: Could not read data!')
    
    uptime = len(data[data[choice]==1])/len(data)
    
    total = len(data[data['Human']==1])/len(data) * (data.iloc[-1]['Timestamp'] - data.iloc[0]['Timestamp'])
    
    return np.abs(data[choice]), uptime

filename = 'O:\\Public\\Yb clock\\180406\\YbI\\logfile.txt'
choice = 'Lattice cavity'

def get_unlocks(filename, choice, start_points = [], end_points = []):
    boolfile = filename.replace('log', 'bool')
    data = pd.read_csv(boolfile,delimiter='\t',index_col = 0)
    data = np.abs(data[choice])
    
    df = pd.Series(index = [])
    for i in range(len(start_points)):
        df = df.append(data.iloc[start_points[i]:end_points[i]])

    durations = []
    unlock_points = df[df.diff()==-1].index.tolist()
    lock_points = df[df.diff()==1].index.tolist()
    for i in range(len(unlock_points)):
        durations.append((lock_points[i] - unlock_points[i])*86400)

    uptime = len(df[df==1]) / len(df) * 100
    print('Number of unlocks: ', len(unlock_points))
    print('Fastest relock: %.0fs.'%np.min(durations))
    print('Slowest relock: %.0fs.'%np.max(durations))
    print('Relocking time: %.0fs +/- %.0fs.'%(np.mean(durations),np.std(durations)))
    print('Uptime: %.1f%%'%uptime)

def count_consecutive_zeros(s):
    v = np.diff(np.r_[0, s.values==0, 0])
    s = pd.value_counts(np.where(v == -1)[0] - np.where(v == 1)[0])
    s.index.name = "num_consecutive_zeros"
    s.name = "count"
    return s

start_points = [0]
end_points = [-1]
get_unlocks(filename, choice, start_points, end_points)

print('\n\nWith glitch removed:')
start_points = [0, 900]
end_points = [750, -1]
get_unlocks(filename, choice, start_points, end_points)