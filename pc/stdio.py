from zope.interface import implements

from twisted.internet import reactor, stdio
from twisted.application.service import Service
from twisted.conch.insults.insults import ServerProtocol
from twisted.conch.insults.insults import ITerminalProtocol

class StdIOController(Service):
    def __init__(self):
        self.protocol = ProtocolSwitcher()
    def startService(self):
        Service.startService(self)
        self.stdio = stdio.StandardIO(ServerProtocol(self.protocol))
    def stopService(self):
        Service.stopService(self)
        self.stdio = None
    def switchTerminalProtocol(self, protocol):
        self.protocol.switch(protocol)

class ProtocolSwitcher:
    implements(ITerminalProtocol)
    def __init__(self):
        self._protocol = None
    def __call__(self):
        return self
    def makeConnection(self, transport):
        assert self._protocol is not None, 'can not makeConnection with no concrete protocol'
        try:
            factory = self.factory
        except AttributeError:
            pass
        else:
            self._protocol.factory = factory
        self._protocol.makeConnection(transport)
    def keystrokeReceived(self, keyID, modifier):
        self._protocol.keystrokeReceived(keyID, modifier)
    def terminalSize(self, width, height):
        self._protocol.terminalSize(width, height)
    def unhandledControlSequence(self, seq):
        self._protocol.unhandledControlSequence(seq)
    def connectionLost(self, reason):
        self._protocol.connectionLost(reason)
    def switch(self, protocol):
        self._protocol = protocol
