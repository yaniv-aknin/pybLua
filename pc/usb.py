from functools import partial

from twisted.internet import reactor
from twisted.internet.threads import deferToThread
from twisted.application.service import Service
from twisted.internet.serialport import SerialPort
from twisted.python import log

from pblua_serial import pbLuaSerialProtocol, pbLuaInitializing, pbLuaConnected, pbLuaLoading
from recipe import loadRecipeLines

def requireState(state):
    def decor(func):
        def callable(self, *args, **kwargs):
            assert self.protocol and self.protocol.state is self.protocol.states[state]
            return func(self, *args, **kwargs)
        callable.__name__ = func.__name__
        callable.__doc__ = func.__doc__
        return callable
    return decor

class USBController(Service):
    def __init__(self, device, baudrate):
        self.device = device
        self.baudrate = baudrate
        self.port = None

    @property
    def protocol(self):
        return self.port.protocol if self.port else None

    def startConnection(self):
        log.msg('opening %s at %s' % (self.device, self.baudrate))
        self.port = SerialPort(pbLuaSerialProtocol(), self.device, reactor, baudrate=self.baudrate)

    def loseConnection(self):
        log.msg('closing %s' % (self.device))
        self.protocol.transport.loseConnection()
        self.port = None

    def startService(self):
        self.startConnection()

    def stopService(self):
        self.loseConnection()

    @requireState(pbLuaConnected)
    def loadRecipe(self, path):
        self.protocol.outgoing = loadRecipeLines(path)
        self.protocol.setState(pbLuaLoading)
