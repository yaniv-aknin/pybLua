from functools import partial

from twisted.conch.manhole import ColoredManhole
from twisted.conch.insults import insults
from twisted.conch.telnet import TelnetTransport, TelnetBootstrapProtocol
from twisted.internet.protocol import ServerFactory

class ManholeTelnetFactory(ServerFactory):
    protocol = lambda self: TelnetTransport(TelnetBootstrapProtocol, insults.ServerProtocol,
                                            partial(ColoredManhole, self.namespace))
    def __init__(self, namespace=None):
        self.namespace = namespace
