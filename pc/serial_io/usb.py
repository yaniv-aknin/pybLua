import os

from twisted.internet import reactor, protocol
from twisted.application.service import Service
from twisted.internet.serialport import SerialPort
from twisted.python import log

from serial.serialutil import SerialException

from protocols.pblua import pbLuaConsoleProtocol

class USBController(Service):
    retries = 6
    interval = 3
    baudrate = 38400
    def __init__(self, device):
        self.device = device
        self.port = None
        self.attempt = None
    @property
    def protocol(self):
        return self.port.protocol if self.port else None
    def startConnection(self):
        self.attempt = 0
        reactor.callWhenRunning(self._startConnection)
    def _startConnection(self):
        self.attempt += 1
        if self.attempt > self.retries:
            log.msg('giving up; USBController remains stopped')
            self.stopService()
            return
        try:
            self.port = SerialPort(pbLuaConsoleProtocol(self), self.device, reactor, baudrate=self.baudrate)
            log.msg('opened %s' % (self.device,))
        except SerialException, error:
            log.err(error)
            log.msg('unable to open %s (%d/%d retries)' % (os.path.basename(self.device), self.attempt, self.retries))
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
    def setState(self, state, *args, **kwargs):
        self.protocol.setState(state, *args, **kwargs)
