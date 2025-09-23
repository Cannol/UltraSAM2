# Here we present two base frameworks for downstream inference applications
# 1. Image/Video reader
# 2. Image/Video reader + visualizer

class TaskBase(object):
    def main(self): raise NotImplementedError()

class AutoReader(TaskBase):
    
    def __init__(self, path_or_file):
        super().__init__()


    def _check_path(self, path):



class Visualizer(AutoReader):

    def __init__(self, path_or_file):
        super().__init__(path_or_file)
