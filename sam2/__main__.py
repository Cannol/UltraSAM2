import sam2.configs as configs
import sam2.core as core

"""
These system-level output are the inner printing functions, if they are annoying you, it can be disabled by
change the "TURNED_ON" to False
"""

TURNED_ON = True
STRENGTH = "1"
NOT_STRENGTH = "0"

class Colors:
    BLACK = "30"
    RED = "31"
    GREEN = "32"
    YELLOW = "33"
    BLUE = "34"
    MAGENTA = "35"
    CYAN = "36"
    WHITE = "37"
    RESET = "39"

def _write2logfile(msg):
    with open(configs.SYSTEM_OUTPUT_LOGS, "a+") as logfile:
        logfile.write(msg+"\n")

if TURNED_ON:
    def SYS_OUT(msg, strength=NOT_STRENGTH, end='\n'):
        print(f"\033[{strength};37m [I] {msg}\033[0m", end=end)
        _write2logfile(msg)

    def SYS_SPECIAL(msg, strength=NOT_STRENGTH, fg=35, end='\n'):
        print(f"\033[{strength};{fg}m {msg}\033[0m", end=end)
        _write2logfile(msg)

    def SYS_ERROR(msg, strength=NOT_STRENGTH, end='\n'):
        print(f"\033[{strength};31m [E] {msg}\033[0m", end=end)
        _write2logfile(msg)
else:
    def SYS_OUT(msg, strength=NOT_STRENGTH, end='\n'): pass
    def SYS_SPECIAL(msg, strength=NOT_STRENGTH, end='\n'): pass
    def SYS_ALARM(msg, strength=NOT_STRENGTH, end='\n'): pass
    def SYS_ERROR(msg, strength=NOT_STRENGTH, end='\n'): pass

SYS_SPECIAL("================ Path Configuration ================")
_paths = configs.Path.get_registered_paths()
for _name, _path in _paths.items():
    SYS_SPECIAL(f"{_name}: {_path}")
SYS_SPECIAL("======================= END ========================")

