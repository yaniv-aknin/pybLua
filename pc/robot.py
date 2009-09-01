import sys
import logging
import tty
import termios
import os

from twisted.internet import reactor
from twisted.python import log, usage
from twisted.conch.stdio import ConsoleManhole

from log import setupLogging

from controller import Controller
from stdio import StdIOController

class RobotOptions(usage.Options):
    optFlags = [
        ['terminal', 't', 'Start in direct terminal mode'],
    ]
    optParameters = [
        ['usb', 'u', None, 'USB Serial device'],
        ['bluetooth', 'b', None, 'Bluetooth Serial device'],
        ['log', 'l', None, 'Path for logfile'],
        ['logLevel', 'L', logging.DEBUG, 'Default loglevel (0-50)'],
    ]
    def postOptions(self):
        for device in ('usb', 'bluetooth'):
            if self[device] is not None:
                continue
            default_device_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.default_' + device)
            if not os.path.islink(default_device_path):
                raise usage.UsageError('no %s device specified and .default_%s symlink missing' % (device, device))
            self[device] = default_device_path
        try:
            self['logLevel'] = int(self['logLevel'])
        except ValueError, error:
            raise usage.UsageError('invalid logLevel %r: %s' % (self['logLevel'], error))

class RawTTYContext:
    def __enter__(self):
        self.fd = sys.__stdin__.fileno()
        self.oldSettings = termios.tcgetattr(self.fd)
        tty.setraw(self.fd)
    def __exit__(self, error_type, error_value, traceback):
        termios.tcsetattr(self.fd, termios.TCSANOW, self.oldSettings)
        os.write(self.fd, "\r\x1bc\r")

def main(argv):
    options = RobotOptions()
    try:
        options.parseOptions(argv[1:])
    except usage.UsageError, errortext:
        print '%s: %s' % (argv[0], errortext)
        print '%s: Try --help for usage details.' % (argv[0])
        raise SystemExit(1)

    setupLogging(options.opts['log'], options.opts['logLevel'])

    with RawTTYContext():
        stdio = StdIOController()
        controller = Controller(options, stdio)
        stdio.protocolStack.push(ConsoleManhole(dict(C=controller, UC=controller.usb, BC=controller.bluetooth)))
        stdio.startService()
        controller.startService()
        reactor.run()
