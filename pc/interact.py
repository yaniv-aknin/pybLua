from functools import partial
import sys
import tty
import termios
import os

from twisted.internet import reactor, stdio
from twisted.application.service import Service
from twisted.conch.insults.insults import ServerProtocol
from twisted.conch.manhole import ColoredManhole
from twisted.conch.insults import insults
from twisted.conch.telnet import TelnetTransport, TelnetBootstrapProtocol
from twisted.internet.protocol import ServerFactory

class ProtocolStack(object):
    # HACK: a crude protocol stack which allows a single transport to have several protocols
    #        this does not handle all sorts of cases, like setattr() on the protocol (it will just be set on the
    #        ProtocolStack instance and never be used) or calling connectionLost() upon self.pop()
    __slots__ = ['push', 'pop', '_protocolStack', 'factory']
    def __init__(self):
        self._protocolStack = []
    def __call__(self):
        return self
    def __getattr__(self, name):
        if not self._protocolStack:
            raise AttributeError('tried gettting an attribute with no concrete protocol')
        return getattr(self._protocolStack[-1], name)
    def __setattr__(self, name, value):
        if name in ('_protocolStack',):
            return super(ProtocolStack, self).__setattr__(name, value)
        if not self._protocolStack:
            raise AttributeError('tried gettting an attribute with no concrete protocol')
        setattr(self._protocolStack[-1], name, value)
    def __nonzero__(self):
        return bool(self._protocolStack)
    def __repr__(self):
        return '<%s using %r>' % (self.__class__.__name__,
                                  None if not self._protocolStack else self._protocolStack[-1])
    def push(self, protocol):
        self._protocolStack.append(protocol)
    def pop(self):
        return self._protocolStack.pop()

class TerminalBridgeProtocol:
    def __init__(self, transport, keyHandlers=None):
        self.transport = transport
        self.keyHandlers = keyHandlers or {}
    def connectionLost(self, reason):
        pass
    def keystrokeReceived(self, keyID, modifier):
        self.keyHandlers.get(keyID, self.transport.write)(keyID)

class InteractionManager:
    def __init__(self):
        self.protocolStack = ProtocolStack()
    def __enter__(self):
        self.fd = sys.__stdin__.fileno()
        self.oldSettings = termios.tcgetattr(self.fd)
        tty.setraw(self.fd)
        return self
    def __exit__(self, error_type, error_value, traceback):
        termios.tcsetattr(self.fd, termios.TCSANOW, self.oldSettings)
        os.write(self.fd, "\r\x1bc\r")
    def takeControl(self, protocol):
        assert not self.protocolStack, 'can not take control before any protocol inserted to interaction protocol stack'
        self.protocolStack.push(protocol)
        self.terminal = stdio.StandardIO(ServerProtocol(self.protocolStack))
