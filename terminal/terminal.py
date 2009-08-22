#!/usr/bin/env python2.6

import sys
import os

import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

from twisted.application import internet
from twisted.internet import reactor
from twisted.python import log, usage

from manhole import ManholeTelnetFactory
from controller import USBController

class TerminalOptions(usage.Options):
    optParameters = [
        ['baudrate', 'b', 38400, 'Serial baudrate [default: 38400]'],
        ['device', 'd', None, 'Serial Port device'],
        ['port', 'p', 2323, 'Port for the Telnet manhole daemon'],
    ]
    def postOptions(self):
        try:
            self['baudrate'] = int(self['baudrate'])
        except ValueError:
            raise options.UsageError('invalid baudrate')

        if self['device'] is None:
            default_device_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.default_device')
            if not os.path.islink(default_device_path):
                raise usage.UsageError('no serial device specified and .default_device symlink missing')
            self['device'] = default_device_path

def main(argv):
    options = TerminalOptions()
    try:
        options.parseOptions(argv[1:])
    except usage.UsageError, errortext:
        print '%s: %s' % (argv[0], errortext)
        print '%s: Try --help for usage details.' % (argv[0])
        raise SystemExit(1)

    log.startLogging(sys.stdout)

    log.msg('Attempting to open %s at %dbps...' % (options.opts['device'], options.opts['baudrate']))

    usbController = UC = USBController(options.opts['device'], options.opts['baudrate'])
    internet.TCPServer(options.opts['port'], ManholeTelnetFactory(locals()),
                       interface='127.0.0.1').startService()
    reactor.run()

if __name__ == '__main__':
    main(sys.argv)
