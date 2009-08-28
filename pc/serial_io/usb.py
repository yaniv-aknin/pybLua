from base import SerialController

from protocols.pblua import pbLuaConsoleProtocol

class USBController(SerialController):
    baudrate = 38400
    defaultProtocolFactory = pbLuaConsoleProtocol
    def setState(self, state, *args, **kwargs):
        self.protocol.setState(state, *args, **kwargs)
