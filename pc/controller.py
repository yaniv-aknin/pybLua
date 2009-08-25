from twisted.application.service import MultiService

from usb import USBController
from stdio import StdIOController, ConsoleManhole

class Controller(MultiService):
    def __init__(self, options):
        MultiService.__init__(self)
        self.usb = USBController(options.opts['device'], options.opts['baudrate'])
        self.usb.setServiceParent(self)
        self.stdio = StdIOController(lambda: ConsoleManhole(dict(C=self, UC=self.usb)))
        self.stdio.setServiceParent(self)
