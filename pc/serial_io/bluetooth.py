from twisted.protocols.basic import Int16StringReceiver
from twisted.internet import defer
from twisted.internet.task import LoopingCall
from twisted.python import log

from base import SerialController

class NAKReceived(Exception):
    pass
class BadCommand(Exception):
    pass

class OPCODES:
    class INCOMING:
        ADD = "A"
        REMOVE = "R"
        EVAL = "E"
    class OUTGOING:
        ACK = "A"
        NAK = "N"
        BAD = "B"
        ASYNC = "X"
        INITIALIZE = "I"

class BluetoothFramingProtocol(Int16StringReceiver):
    def __init__(self, parent):
        self.parent = parent
        self.upperProtocol = BluetoothProtocol(self)
    def connectionMade(self):
        self.upperProtocol.connectionMade()
    def stringReceived(self, data):
        self.upperProtocol.stringReceived(data)
    def connectionLost(self, reason):
        self.upperProtocol.connectionLost()
        log.err(reason)

def OPCODE(opcode, expectedState=None):
    def decor(func):
        func.opcode = opcode
        func.expectedState = expectedState
        return func
    return decor

class BluetoothProtocol:
    opcodes = {}
    magic = 'pybLua-1'
    class __metaclass__(type):
        def __init__(cls, name, bases, env):
            for key, value in env.items():
                if hasattr(value, 'opcode'):
                    cls.opcodes[value.opcode] = value
        def __str__(cls):
            return cls.__name__
    def __init__(self, framing):
        self.framing = framing
        self.state = None
        self.outgoingQueue = []
        self.commandReceivedDeferred = None
        self.heartbeatTimer = None
        self.heartbeats = None
    def connectionMade(self):
        self.state = 'initializing'
        self.heartbeats = 0
    def connectionLost(self):
        if self.heartbeatTimer:
            self.heartbeatTimer.stop()
    def stringReceived(self, data):
        opcode, payload = data[0], data[1:]
        func = self.opcodes.get(opcode, self.invalidOpcode)
        if func.expectedState and self.state != func.expectedState:
            self.invalidState(opcode, payload, func.expectedState)
            return
        func(self, payload)
    @OPCODE(None)
    def invalidOpcode(self, opcode, payload):
        log.msg('received unknown opcode %s with payload %s' % (opcode, payload))
    def invalidState(self, opcode, payload, expectedState):
        log.msg('ignoring opcode %s with payload %s; state is %s and expected %s' %
                (opcode, payload, self.state, expectedState))
    def sendCommand(self, command, deferred):
        self.state = 'command-sent'
        self.commandReceivedDeferred = deferred
        self.framing.sendString(command)
    def doCommand(self, command, deferred=None):
        if self.state == 'idle':
            self.sendCommand(command, deferred)
        else:
            self.outgoingQueue.append((command, deferred))
    @OPCODE('A', 'command-sent')
    def acknowledgment(self, payload):
        self.state = 'idle'
        if self.commandReceivedDeferred:
            self.commandReceivedDeferred.callback(payload)
        if self.outgoingQueue:
            self.sendCommand(*self.outgoingQueue.pop(-1))
    @OPCODE('N', 'command-sent')
    def nonAcknowledgment(self, payload):
        self.state = 'idle'
        if self.commandReceivedDeferred:
            self.commandReceivedDeferred.errback(NAKReceived(payload))
        if self.outgoingQueue:
            self.sendCommand(*self.outgoingQueue.pop(-1))
    @OPCODE('B', 'command-sent')
    def badCommand(self, payload):
        self.state = 'idle'
        log.msg('BAD: %s' % (payload,))
        if self.commandReceivedDeferred:
            self.commandReceivedDeferred.errback(BadCommand(payload))
        if self.outgoingQueue:
            self.sendCommand(*self.outgoingQueue.pop(-1))
    @OPCODE('X')
    def asyncResponse(self, payload):
        log.msg('received async response: %s' % (payload,))
    @OPCODE('I', 'initializing')
    def initialize(self, payload):
        if not payload.startswith(self.magic):
            log.msg('warning: initialized with wrong protocol magic: %r (expected %r)' % (payload, self.magic))
        log.msg('initialized by %s' % (payload,))
        self.state = 'idle'
        self.heartbeatTimer = LoopingCall(self.sendHeartbeat)
        self.heartbeatTimer.start(0.1)
    def sendHeartbeat(self):
        self.doCommand('H', defer.Deferred().addCallback(self.heatbeatReceived))
    def heatbeatReceived(self, payload):
        self.heartbeats += 1
        self.freeRAM = int(payload)

class BluetoothController(SerialController):
    baudrate = 115200
    defaultProtocolFactory = BluetoothFramingProtocol
