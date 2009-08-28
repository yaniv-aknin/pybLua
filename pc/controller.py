from twisted.application.service import MultiService
from twisted.conch.stdio import ConsoleManhole
from twisted.conch.manhole import CTRL_D
from twisted.conch.insults.insults import ServerProtocol

from usb import USBController
from stdio import StdIOController
from protocol_utils import TerminalBridgeProtocol, BridgeProtocol

class Controller(MultiService):
    def __init__(self, options):
        MultiService.__init__(self)
        self.options = options
        self.usb = USBController(options.opts['device'], options.opts['baudrate'])
        self.usb.setServiceParent(self)
        self.stdio = StdIOController()
        self.stdio.protocolStack.push(ConsoleManhole(dict(C=self, SC=self.stdio, UC=self.usb)))
        self.stdio.setServiceParent(self)
    def startService(self):
        MultiService.startService(self)
        if self.options.opts['terminal']:
            self.terminal()
    def terminal(self):
        self.stdio.protocolStack.push(TerminalBridgeProtocol(self.usb.port, {CTRL_D: self.manhole}))
        self.usb.protocolStack.push(BridgeProtocol(self.stdio.stdio))
    def manhole(self, keyID):
        self.stdio.protocolStack.pop()
        self.usb.protocolStack.pop()
