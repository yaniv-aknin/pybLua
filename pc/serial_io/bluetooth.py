from twisted.protocols.basic import Int16StringReceiver
from twisted.python import log

from base import SerialController

class BluetoothFramingProtocol(Int16StringReceiver):
    def __init__(self, parent):
        self.parent = parent
    def connectionMade(self):
        log.msg('connectionMade')
    def stringReceived(self, data):
        log.msg('data: %s' % data)
    def connectionLost(self, reason):
        log.err(reason)

class BluetoothController(SerialController):
    baudrate = 115200
    defaultProtocolFactory = BluetoothFramingProtocol
