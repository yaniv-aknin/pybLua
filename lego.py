#!/usr/bin/env python2.6
from __future__ import print_function

import warnings
import sys
import os

warnings.filterwarnings('ignore', category=DeprecationWarning)

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


if __name__ == '__main__':
    if len(sys.argv) == 1 or sys.argv[1] == 'robot':
        from pc.robot import main
    elif sys.argv[1] == 'logserver':
        from yalib.logutils.server import main
    else:
        print('unknown subcommand %s' % (sys.argv[1],))
    main([sys.argv[0]] + sys.argv[2:])
