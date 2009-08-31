from base import SerialController
from pyblua.protocol import pybLuaProtocol

class BluetoothController(SerialController):
    baudrate = 115200
    defaultProtocolFactory = pybLuaProtocol
