from base import SerialController

from pblua_protocol import pbLuaConsoleProtocol

class USBController(SerialController):
    baudrate = 19200
    defaultProtocolFactory = pbLuaConsoleProtocol
    def setState(self, state, *args, **kwargs):
        self.protocol.setState(state, *args, **kwargs)
