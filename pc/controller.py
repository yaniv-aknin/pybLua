from twisted.internet import reactor
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

    def startService(self):
        log.msg('Attempting to open %s at %dbps...' % (self.device, self.baudrate))
        self.port = SerialPort(pbLuaSerialProtocol(), self.device, reactor, baudrate=self.baudrate)

    @requireState(pbLuaConnected)
    def loadRecipe(self, path):
        self.protocol.outgoing = loadRecipeLines(path)
        self.protocol.setState(pbLuaLoading)
