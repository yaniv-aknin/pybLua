from twisted.internet.protocol import Protocol
from twisted.python import log

class pbLuaSerialProtocol(Protocol):
    knownStates = []
    def __init__(self):
        self.states = dict((cls, cls(self)) for cls in self.knownStates)
        self.state = None
    def setState(self, state):
        if self.state is not None:
            self.state.exit()
        self.state = self.states[state]
        self.state.enter()
    def connectionMade(self):
        self.setState(pbLuaInitializing)
    def dataReceived(self, data):
        return self.state.dataReceived(data)
    def connectionLost(self, reason):
        return self.state.connectionLost(reason)

class pbLuaState:
    def __init__(self, parent):
        self.parent = parent
        self.transport = parent.transport
    def enter(self):
        log.msg('settings state: %s' % (self.__class__.__name__,))
    def exit(self):
        pass
    def connectionMade(self):
        pass
    def dataReceived(self, data):
        pass
    def connectionLost(self, reason):
        pass
    @staticmethod
    def decorate(cls):
        pbLuaSerialProtocol.knownStates.append(cls)
        return cls

@pbLuaState.decorate
class pbLuaInitializing(pbLuaState):
    def enter(self):
        pbLuaState.enter(self)
        self.parent.transport.write('\n')
    def dataReceived(self, data):
        if data.strip() == '>':
            self.parent.setState(pbLuaConnected)
        else:
            log.msg('desired prompt, received %r instead' % (data,))
    def connectionLost(self, reason):
        log.msg('init connection lost: %s' % (reason,))

@pbLuaState.decorate
class pbLuaConnected(pbLuaState):
    def dataReceived(self, data):
        log.msg('received: ' + data.strip())
    def connectionLost(self, reason):
        log.msg('connected connection lost: %s' % (reason,))
