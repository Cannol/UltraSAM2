# Here we configure and store all the critical paths/files or settings for our system
# The path/files are arranged by relative path, while the absolute path is not suggested
#     here for inflexible reasons.
import inspect
from datetime import datetime
from os.path import join, dirname, abspath, isfile
from os import makedirs

from typing_extensions import LiteralString

class Path:
    _registered_paths = {}
    def __init__(self, root_path, path_name=None) -> None:
        self._root = root_path
        if path_name is not None:
            self._registered_paths[path_name] = root_path

    def __call__(self, *add_path_relative: str) -> str:
        return str(join(self._root, *add_path_relative))

    def __str__(self) -> str: return self._root

    def value(self) -> str: return self._root

    def __add__(self, other) -> "Path": return Path(join(self._root, str(other)))

    @property
    def isfile(self): return isfile(self._root)

    def create(self, exist_ok=True) -> "Path":
        if not isfile(self._root): makedirs(self._root, exist_ok=exist_ok)
        return self

    @classmethod
    def get_registered_paths(cls) -> dict[str, "Path"]: return cls._registered_paths

def get_timestamp_now() -> str: 
    now = datetime.now(); return now.strftime("%Y%m%d_%H%M%S") + f"{int(now.microsecond/1000):03d}"

# The relative path is based on the system (project) root path
ProjectPath = abspath(join(dirname(__file__), "..", "..")); R = Path(ProjectPath, "ProjectPath")
SAM_ROOT = R("sam2")
ConfigPath = join(SAM_ROOT, "configs"); C = Path(ConfigPath, "ConfigPath")
ModulePath = join(SAM_ROOT, "modules"); M = Path(ModulePath, "ModulePath")
TaskPath = join(SAM_ROOT, "tasks"); T = Path(TaskPath, "TaskPath")

# Extra output paths
OutputPath = R("outputs", get_timestamp_now()); O = Path(OutputPath, "OutputPath")
LogsPath = O("logs"); L = Path(LogsPath, "LogsPath").create()

# Real path constructed below:
LOGGER_CONFIG_FILE = C("logger.json")
SYSTEM_OUTPUT_LOGS = L("system-output-logs.log")

# Shared Space path
SharedSpacePath = R(".shared_space"); S = Path(SharedSpacePath, "SharedSpacePath")
SequenceCachePath = S("sequences"); Q = Path(SequenceCachePath, "SequenceCachePath").create()

