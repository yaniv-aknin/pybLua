#!/usr/bin/env python2.6
from __future__ import print_function

import warnings
import sys
import os

warnings.filterwarnings('ignore', category=DeprecationWarning)

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lib.main import invokables

import pc.robot

if __name__ == '__main__':
    if len(sys.argv) == 1 or sys.argv[1] not in invokables:
        sys.exit(print('usage: %s <%s> [...]' % (sys.argv[0], ", ".join(invokables))))
    invokables[sys.argv[1]](sys.argv[1:])
