from base import SerialController
from pyblua_protocol import pybLuaProtocol

class BluetoothController(SerialController):
    baudrate = 115200
    defaultProtocolFactory = pybLuaProtocol
