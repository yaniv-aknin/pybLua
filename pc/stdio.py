from twisted.internet import reactor, stdio
from twisted.application.service import Service
from twisted.conch.insults.insults import ServerProtocol

from protocol_utils import ProtocolSwitcher

class StdIOController(Service):
    def __init__(self):
        self.switcher = ProtocolSwitcher()
    def startService(self):
        Service.startService(self)
        self.stdio = stdio.StandardIO(ServerProtocol(self.switcher))
    def stopService(self):
        Service.stopService(self)
        self.stdio = None
    def switchTerminalProtocol(self, protocol):
        self.switcher.switch(protocol)
