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

    def from_json(self, block_dict, subblock=None):
        ''' Recursively constructs blocks and subpipelines to prepare a pipeline
            from the passed dict. '''
        if subblock is None:
            subblock = self
        for b in block_dict:
            block = getattr(importlib.import_module('emergent.pipeline'), b['block'])
            if 'params' not in b:
                b['params'] = {}
            block = block(b['params'])
            subblock.add(block)

            if 'subblocks' in b:
                self.from_json(b['subblocks'], subblock=block)

    def to_json(self, pipeline=None):
        ''' Recursively converts all blocks and subpipelines to a representative
            dict '''
        if pipeline is None:
            pipeline = self
        lst = []
        for block in pipeline.blocks:
            if issubclass(block.__class__, BasePipeline):
                name = block.__class__.__name__
                lst.append({'block': name,
                            'params': {k: v.value for k, v in block.params.items()},
                            'subblocks': self.to_json(pipeline=block)})
            else:
                block_dict = {'block': block.__class__.__name__, 'params': {}}
                for p in block.params:
                    block_dict['params'][p] = block.params[p].value
                lst.append(block_dict)
        return lst
