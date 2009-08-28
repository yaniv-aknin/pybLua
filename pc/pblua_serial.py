from functools import partial

from twisted.internet.protocol import Protocol
from twisted.python import log

class InvalidTransition(Exception):
    pass

def isPrompt(data):
    data = data.splitlines()[-1].strip()
    return data in ('>', '>>')

class pbLuaSerialProtocol(Protocol):
    knownStates = []
    def __init__(self, parent):
        self.parent = parent
        self.states = dict((cls, cls(self)) for cls in self.knownStates)
        self.state = None
        self.outgoing = []
    def setState(self, state):
        if state.enterFrom and self.state.__class__ not in state.enterFrom:
            raise InvalidTransition('invalid state change: %s -> %s' % (self.state, state))
        log.msg('state: %s -> %s' % (self.state, state))
        if self.state is not None:
            self.state.exit()
        previousState = self.state
        self.state = self.states[state]
        self.state.enter(previousState)
    def connectionMade(self):
        self.setState(pbLuaInitializing)
    def dataReceived(self, data):
        return self.state.dataReceived(data)
    def connectionLost(self, reason):
        return self.state.connectionLost(reason)

class pbLuaState:
    enterFrom = tuple()
    class __metaclass__(type):
        def __init__(cls, name, bases, env):
            pbLuaSerialProtocol.knownStates.append(cls)
        def __str__(cls):
            return cls.__name__
    def __init__(self, parent):
        self.parent = parent
        self.transport = parent.transport
    def __str__(self):
        return self.__class__.__name__
    def enter(self, previousState):
        pass
    def exit(self):
        pass
    def connectionMade(self):
        pass
    def dataReceived(self, data):
        pass
    def connectionLost(self, reason):
        pass

class pbLuaInitializing(pbLuaState):
    def enter(self, previousState):
        pbLuaState.enter(self, previousState)
        self.parent.transport.write('\n')
    def dataReceived(self, data):
        if isPrompt(data):
            self.parent.setState(pbLuaConnected)
        else:
            log.msg('desired prompt, received %r instead' % (data,))
    def connectionLost(self, reason):
        log.msg('init connection lost: %s' % (reason,))

class pbLuaConnected(pbLuaState):
    def dataReceived(self, data):
        log.msg('received: ' + data.strip())
    def connectionLost(self, reason):
        log.msg('connected connection lost: %s' % (reason,))

class pbLuaLoading(pbLuaState):
    enterFrom=(pbLuaConnected,)
    def enter(self, previousState):
        pbLuaState.enter(self, previousState)
        self.sendLine()
    def sendLine(self):
        line = self.parent.outgoing.pop(0)
        log.msg('sent: ' + line)
        self.parent.transport.write(line + '\n')
    def dataReceived(self, data):
        if not isPrompt(data):
            return
        if self.parent.outgoing:
            self.sendLine()
        else:
            self.parent.setState(pbLuaConnected)
    def connectionLost(self, reason):
        log.msg('loading connection lost: %s' % (reason,))

class pbLuaTerminal(pbLuaState):
    enterFrom=(pbLuaConnected,)
    def dataReceived(self, data):
        self.parent.parent.parent.stdio.transport.write(data)
