from twisted.protocols.basic import LineReceiver
from twisted.python import log

from errors import InvalidTransition
from base import StateMachineMixin

class pbLuaConsoleProtocol(LineReceiver, StateMachineMixin):
    knownStates = []
    def __init__(self, parent):
        self.parent = parent
        StateMachineMixin.__init__(self)
    def connectionMade(self):
        from pblua_states import pbLuaInitializing
        self.setState(pbLuaInitializing)
    def rawDataReceived(self, data):
        return self.state.dataReceived(data)
    def lineReceived(self, line):
        return self.state.lineReceived(line)
    def connectionLost(self, reason):
        return self.state.connectionLost(reason)

