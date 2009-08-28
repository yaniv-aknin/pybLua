from functools import partial

from twisted.internet import reactor, protocol
from twisted.internet.threads import deferToThread
from twisted.application.service import Service
from twisted.internet.serialport import SerialPort
from twisted.python import log

from pblua_serial import pbLuaSerialProtocol, pbLuaLoading
from recipe import loadRecipeLines
from protocol_utils import ProtocolStack

class USBController(Service):
    def __init__(self, device, baudrate, initialProtocolFactory=pbLuaSerialProtocol):
        self.device = device
        self.baudrate = baudrate
        self.port = None
        self.protocolStack = ProtocolStack(initialProtocolFactory(self))
    @property
    def protocol(self):
        return self.port.protocol if self.port else None
    def startConnection(self):
        log.msg('opening %s at %s' % (self.device, self.baudrate))
        self.port = SerialPort(self.protocolStack, self.device, reactor, baudrate=self.baudrate)
    def loseConnection(self):
        log.msg('closing %s' % (self.device))
        self.protocol.transport.loseConnection()
        self.port = None
    def startService(self):
        Service.startService(self)
        self.startConnection()
    def stopService(self):
        Service.stopService(self)
        self.loseConnection()
    def loadRecipe(self, path):
        self.protocol.outgoing = loadRecipeLines(path)
        self.protocol.setState(pbLuaLoading)
