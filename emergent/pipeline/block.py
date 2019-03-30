class Block():
    def __init__(self):
        self.pipeline, self.source = (None, None)

    def connect(self, pipeline):
        self.pipeline = pipeline
        self.source = pipeline.source
