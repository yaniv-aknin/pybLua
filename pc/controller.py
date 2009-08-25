from twisted.application.service import MultiService
from twisted.conch.stdio import ConsoleManhole

from usb import USBController
from stdio import StdIOController

class Controller(MultiService):
    def __init__(self, options):
        MultiService.__init__(self)
        self.usb = USBController(options.opts['device'], options.opts['baudrate'])
        self.usb.setServiceParent(self)
        self.stdio = StdIOController()
        self.stdio.switchTerminalProtocol(ConsoleManhole(dict(C=self, SC=self.stdio, UC=self.usb)))
        self.stdio.setServiceParent(self)
