import os

from twisted.application.service import MultiService
from twisted.conch.stdio import ConsoleManhole
from twisted.conch.manhole import CTRL_D
from twisted.conch.insults.insults import ServerProtocol

from usb import USBController
from stdio import StdIOController
from protocol_utils import TerminalBridgeProtocol
from pblua_serial import pbLuaRunning, pbLuaTerminal, pbLuaLoading, pbLuaInitializing
from recipe import loadRecipeLines

class Controller(MultiService):
    def __init__(self, options):
        MultiService.__init__(self)
        self.options = options
        self.usb = USBController(options.opts['usb'])
        self.usb.setServiceParent(self)
        self.stdio = StdIOController()
        self.stdio.protocolStack.push(ConsoleManhole(dict(C=self, SC=self.stdio, UC=self.usb)))
        self.stdio.setServiceParent(self)
    def startService(self):
        MultiService.startService(self)
        if self.options.opts['terminal']:
            self.terminal()
    def load(self, path):
        from lego import PROJECT_ROOT
        if os.path.isfile(os.path.join(PROJECT_ROOT, 'nxt', path)):
            path = (os.path.join(PROJECT_ROOT, 'nxt', path))
        self.usb.setState(pbLuaLoading, loadRecipeLines(path))
    def terminal(self):
        self.stdio.protocolStack.push(TerminalBridgeProtocol(self.usb.port, {CTRL_D: self.manhole}))
        self.usb.setState(pbLuaTerminal, self.stdio.stdio)
    def manhole(self, keyID):
        self.stdio.protocolStack.pop()
        self.usb.setState(pbLuaInitializing)
    def execute(self):
        self.usb.protocol.setState(pbLuaRunning)
