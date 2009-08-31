from twisted.python import log
from twisted.internet.defer import Deferred

from base import State
from pyblua_commands import Heartbeat
from pyblua_errors import NAKReceived, InternalError

def OPCODE(opcode):
    def decor(func):
        func.opcode = opcode
        return func
    return decor

class pybLuaState(State):
    opcodes = {}
    class __metaclass__(type):
        def __init__(cls, name, bases, env):
            from pyblua_protocol import pybLuaProtocol
            pybLuaProtocol.knownStates.append(cls)
            for key, value in env.items():
                if hasattr(value, 'opcode'):
                    cls.opcodes[value.opcode] = value
            for base in bases:
                for key, value in base.__dict__.iteritems():
                    if hasattr(value, 'opcode'):
                        cls.opcodes[value.opcode] = value
        def __str__(cls):
            return cls.__name__

class pybLuaInitializing(pybLuaState):
    def enter(self, previousState):
        pybLuaState.enter(self, previousState)
        self.parent.heartbeats = 0
    @OPCODE('I')
    def initialize(self, payload):
        if not payload.startswith(self.parent.magic):
            log.msg('warning: initialized with wrong protocol magic: %r (expected %r)' % (payload, self.magic))
        log.msg('%s initialized by %s' % (self, payload,))
        self.parent.setState(pybLuaIdle)

class pybLuaAsyncState(pybLuaState):
    @OPCODE('E')
    def internalError(self, payload):
        log.err(InternalError(self, payload))

class pybLuaIdle(pybLuaState):
    noisy = False
    def enter(self, previousState):
        pybLuaState.enter(self, previousState)
        self.attempts = 0
        self.parent.setAlarm(self.parent.heartbeatIntervalSeconds, self.sendHeartbeat)
    def sendHeartbeat(self):
        self.parent.setState(pybLuaBusy,
                      Heartbeat(Deferred().addCallbacks(self.parent.heartbeatReceived, self.parent.heatbeatMissed)))
    def exit(self, nextState):
        self.parent.cancelAlarm(swallowErrors=True)

class pybLuaBusy(pybLuaState):
    noisy = False
    def enter(self, previousState, command):
        pybLuaState.enter(self, previousState)
        self.sendCommand(command)
    def sendCommand(self, command):
        self.command = command
        self.parent.sendCommand(command)
    @OPCODE('A')
    def acknowledgment(self, payload):
        self.command.result.callback(payload)
        self.commandFinished()
    @OPCODE('N')
    def nonAcknowledgment(self, payload):
        self.command.result.errback(NAKReceived(self.command, payload))
        self.commandFinished()
    def commandFinished(self):
        if self.parent.outgoingQueue:
            self.sendCommand(self.parent.outgoingQueue.pop(-1))
        else:
            self.parent.setState(pybLuaIdle)
    def exit(self, nextState):
        self.command = None
