from twisted.internet import reactor
from twisted.application.service import Service
from twisted.internet.serialport import SerialPort

from pblua_serial import pbLuaSerialProtocol

class USBController(Service):
    def __init__(self, device, baudrate):
        self.device = device
        self.baudrate = baudrate
        self.port = None
    @property
    def protocol(self):
        return self.port.protocol if self.protocol else None
    def startService(self):
        self.port = SerialPort(pbLuaSerialProtocol(), self.device, reactor, baudrate=self.baudrate)
