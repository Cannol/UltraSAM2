from sam2.core import TaskBase




class AutoReader(TaskBase):
    
    def __init__(self, path):
        super().__init__()
        self.