#!/usr/bin/env python2.6
from __future__ import print_function

import warnings
import sys
import os

warnings.filterwarnings('ignore', category=DeprecationWarning)

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

__version__ = (0, 0, 1)
__version_str__ = ".".join(str(element) for element in __version__)

from yalib.mainutils.usage import parse_arguments, executable

# import all modules where executable classes exist
import pc.robot

# register the Logserver explicitly as an executable
from yalib.logutils.server import Logserver
Logserver = executable(Logserver)

if __name__ == '__main__':
    options = parse_arguments(sys.argv)
    options.executable(options).invoke()
