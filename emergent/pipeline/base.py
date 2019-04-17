import numpy as np
import importlib
import inspect
import matplotlib.pyplot as plt
import logging as log
import time
from abc import abstractmethod

class BasePipeline:
    def __init__(self):
        self.blocks = []
        self.points = np.atleast_2d([])
        self.costs = np.array([])

    def add(self, block):
        self.blocks.append(block)
        block.pipeline = self
        block.number = len(self.blocks)

        return block

    @abstractmethod
    def measure(self, point):
        return

    def from_json(self, block_dict):
        for b in block_dict:
            block = getattr(importlib.import_module('emergent.pipeline'), b['block'])
            if 'params' not in b:
                b['params'] = {}
            self.add(block(b['params']))

    def to_json(self):
        lst = []
        for block in self.blocks:
            block_dict = {'block': block.__class__.__name__, 'params': {}}
            for p in block.params:
                block_dict['params'][p] = block.params[p].value
            lst.append(block_dict)
        return lst
        
