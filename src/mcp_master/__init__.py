import os
import sys

module_paths = ["./", "./mcp"]
file_path = os.path.dirname(__file__)
os.chdir(file_path)

for module_path in module_paths:
    full_path = os.path.normpath(os.path.join(file_path, module_path))
    sys.path.append(full_path)

from config import set_config
from master_server import MasterMCPServer

__all__ = [MasterMCPServer, set_config]
