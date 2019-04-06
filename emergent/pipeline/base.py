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
