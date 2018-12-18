import sys
import os
import pickle

class Network():
    def __init__(self):
        self.name = sys.argv[1]
        self.path='networks/%s'%sys.argv[1]
        self.data_path = self.path+'/data/'

    def load_task(self):
        files = os.listdir(self.data_path)
        files = [x for x in files if '.sci' in x]
        print(files)

        file = files[0]
        with open(self.data_path+file, 'rb') as f:
            sampler = pickle.load(f)
        sampler.start_time = None

        return sampler
