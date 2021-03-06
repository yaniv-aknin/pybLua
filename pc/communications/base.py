import os
import logging

from twisted.internet import reactor, protocol
from twisted.application.service import Service
from twisted.internet.serialport import SerialPort
from twisted.python import log

from serial.serialutil import SerialException

from errors import InvalidTransition

class SerialController(Service):
    retries = 6
    interval = 3
    baudrate=9600
    def __init__(self, device, protocolFactory=None):
        self.device = device
        self.port = None
        self.attempt = None
        assert hasattr(self, 'defaultProtocolFactory'), 'subclasses should specify defaultProtocolFactory'
        self.protocolFactory = protocolFactory or self.defaultProtocolFactory
    @property
    def protocol(self):
        return self.port.protocol if self.port else None
    def startConnection(self):
        self.attempt = 0
        reactor.callWhenRunning(self._startConnection)
    def _startConnection(self):
        self.attempt += 1
        if self.attempt > self.retries:
            log.msg('giving up; %s remains stopped' % (self.__class__.__name__,), logLevel=logging.WARNING)
            self.stopService()
            return
        try:
            self.port = SerialPort(self.protocolFactory(self), self.device, reactor, baudrate=self.baudrate)
            log.msg('opened %s' % (self.device,))
        except SerialException, error:
            log.msg('unable to open %s (%d/%d retries)' % (os.path.basename(self.device), self.attempt, self.retries),
                    logLevel=logging.WARNING)
            reactor.callLater(self.interval, self._startConnection)
    def tearConnection(self):
        log.msg('closing %s' % (self.device))
        self.protocol.transport.loseConnection()
        self.port = None
    def startService(self):
        Service.startService(self)
        self.startConnection()
    def stopService(self):
        Service.stopService(self)
        if self.port is not None:
            self.tearConnection()

class State(object):
    logLevel = 10
    enterFrom = tuple()
    def __init__(self, parent):
        self.parent = parent
        self.transport = parent.transport
    def __str__(self):
        return self.__class__.__name__
    def enter(self, previousState):
        pass
    def exit(self, nextState):
        pass
    def connectionMade(self):
        pass
    def lineReceived(self, line):
        log.msg('%s received: %s' % (self, line))
    def dataReceived(self, data):
        log.msg('%s received: %s' % (self, data))
    def connectionLost(self, reason):
        log.msg('%s lost connection: %s' % (self, reason))
        log.err(reason)

class StateMachineMixin:
    """This class can be mixed with protocols to facilitate the creation of state-machine controlled protocols"""
    def __init__(self):
        self.states = dict((cls, cls(self)) for cls in self.knownStates)
        self.state = None
    def setState(self, state, *args, **kwargs):
        if state.enterFrom and self.state.__class__ not in state.enterFrom:
            raise InvalidTransition('invalid state change: %s -> %s' % (self.state, state))
        log.msg('%s: %s -> %s' % (self.__class__.__name__, self.state, state), logLevel = state.logLevel)
        if self.state is not None:
            self.state.exit(state)
        previousState = self.state
        self.state = self.states[state]
        self.state.enter(previousState, *args, **kwargs)
