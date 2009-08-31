from twisted.protocols.basic import Int16StringReceiver
from twisted.internet import reactor
from twisted.python import log
from twisted.internet.error import AlreadyCalled, AlreadyCancelled

from base import StateMachineMixin

from pyblua_errors import BadOpcode

# HACK: also inherit object to allow the metaclass to exist; maybe its a bad idea
class pybLuaProtocol(Int16StringReceiver, StateMachineMixin):
    IReactorTimeProvider = reactor
    magic = 'pybLua-1'
    heartbeatIntervalSeconds = 0.5
    maximumMissedHeartbeats = 3
    knownStates = []
    def __init__(self, parent):
        StateMachineMixin.__init__(self)
        self.parent = parent
        self.alarm = None
        self.heartbeats = None
        self.consecutiveHeartbeatsMissed = None
        self.usedBytes = None
        self.outgoingQueue = []
    def connectionMade(self):
        from pyblua_states import pybLuaInitializing
        self.consecutiveHeartbeatsMissed = 0
        self.setState(pybLuaInitializing)
    def connectionLost(self, reason):
        self.state.connectionLost(reason)
        self.heartbeats = None
        self.usedBytes = None
        self.cancelAlarm(swallowErrors=True)
        self.outgoingQueue = []
    def stringReceived(self, data):
        log.msg('rcvd: %s' % (data))
        opcode, payload = data[0], data[1:]
        func = self.state.opcodes.get(opcode)
        if func is None:
            log.err(BadOpcode(self.state, data))
        else:
            func(self.state, payload)
    def sendCommand(self, command):
        log.msg(str(command))
        self.sendString(str(command))
    def setAlarm(self, timeout, callable, *args, **kwargs):
        assert self.alarm is None or self.alarm.called, 'trying to set an alarm on an already set alarm'
        self.alarm = self.IReactorTimeProvider.callLater(timeout, callable, *args, **kwargs)
    def doCommand(self, command):
        from pyblua_states import pybLuaIdle, pybLuaBusy
        if self.state is pybLuaIdle:
            self.setState(pybLuaBusy, command)
        else:
            self.outgoingQueue.append(command)
    def cancelAlarm(self, swallowErrors=False):
        try:
            self.alarm.cancel()
        except (AlreadyCalled, AlreadyCancelled):
            if not swallowErrors:
                raise
        except AttributeError:
            if not swallowErrors:
                raise AlreadyCancelled('trying to cancel a non-existent alarm')
    def heartbeatReceived(self, payload):
        self.consecutiveHeartbeatsMissed = 0
        self.heartbeats += 1
        self.usedBytes = int(payload)
    def heatbeatMissed(self, failure):
        log.err(failure)
        self.consecutiveHeartbeatsMissed += 1
        if self.consecutiveHeartbeatsMissed > self.maximumMissedHeartbeats:
            self.transport.loseConnection()
