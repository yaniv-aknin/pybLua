#!/usr/bin/env python2.6
from __future__ import print_function

import warnings
import sys
import os

warnings.filterwarnings('ignore', category=DeprecationWarning)

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pc.robot import main

if __name__ == '__main__':
    main(sys.argv)
