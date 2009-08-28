from twisted.internet import reactor, stdio
from twisted.application.service import Service
from twisted.conch.insults.insults import ServerProtocol

from protocol_utils import ProtocolStack

class StdIOController(Service):
    def __init__(self):
        self.protocolStack = ProtocolStack()
    def startService(self):
        Service.startService(self)
        self.stdio = stdio.StandardIO(ServerProtocol(self.protocolStack))
    def stopService(self):
        Service.stopService(self)
        self.stdio = None
