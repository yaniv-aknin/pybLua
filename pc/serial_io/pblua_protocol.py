from twisted.protocols.basic import LineReceiver
from twisted.python import log

class pbLuaConsoleProtocol(LineReceiver):
    knownStates = []
    def __init__(self, parent):
        self.parent = parent
        self.states = dict((cls, cls(self)) for cls in self.knownStates)
        self.state = None
        self.outgoing = []
    def setState(self, state, *args, **kwargs):
        if state.enterFrom and self.state.__class__ not in state.enterFrom:
            raise InvalidTransition('invalid state change: %s -> %s' % (self.state, state))
        log.msg('state: %s -> %s' % (self.state, state))
        if self.state is not None:
            self.state.exit(state)
        previousState = self.state
        self.state = self.states[state]
        self.state.enter(previousState, *args, **kwargs)
    def connectionMade(self):
        from pblua_states import pbLuaInitializing
        self.setState(pbLuaInitializing)
    def rawDataReceived(self, data):
        return self.state.dataReceived(data)
    def lineReceived(self, line):
        return self.state.lineReceived(line)
    def connectionLost(self, reason):
        return self.state.connectionLost(reason)

