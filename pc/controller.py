from __future__ import print_function
import os

from twisted.application.service import MultiService
from twisted.conch.manhole import CTRL_D
from twisted.conch.insults.insults import ServerProtocol
from twisted.python import log
from twisted.internet.defer import Deferred

from communications.usb import USBController
from communications.bluetooth import BluetoothController
from communications.pblua.states import pbLuaRunning, pbLuaTerminal, pbLuaLoading, pbLuaInitializing
from communications.pyblua.states import pybLuaInitializing
from communications.pyblua.commands import Evaluate
from interact import TerminalBridgeProtocol
from recipe import loadRecipeLines

class Controller(MultiService):
    def __init__(self, usbDevice, bluetoothDevice, interactionController):
        MultiService.__init__(self)
        self.usb = USBController(usbDevice)
        self.usb.setServiceParent(self)
        self.bluetooth = BluetoothController(bluetoothDevice)
        self.interactionController = interactionController
    def load(self, path='master.recipe'):
        from lego import PROJECT_ROOT
        if os.path.isfile(os.path.join(PROJECT_ROOT, 'nxt', path)):
            path = (os.path.join(PROJECT_ROOT, 'nxt', path))
        self.usb.setState(pbLuaLoading, loadRecipeLines(path))
    def terminal(self):
        self.interactionController.protocolStack.push(TerminalBridgeProtocol(self.usb.port, {CTRL_D: self.manhole}))
        self.usb.setState(pbLuaTerminal, self.interactionController.terminal)
    def manhole(self, keyID):
        self.interactionController.protocolStack.pop()
        self.usb.setState(pbLuaInitializing)
    def execute(self):
        self.usb.protocol.setState(pbLuaRunning)
    def eval(self, luaCode, addReturn=True):
        d = Deferred().addCallbacks(lambda value: log.msg('eval: ' + repr(value)), log.err)
        self.bluetooth.protocol.doCommand(Evaluate(d, ('return ' + luaCode) if addReturn else luaCode))
    def buttonBeep(self):
        self.eval('nxt.InputSetType(1, 1, 0x20)')
        self.eval(
                  'r:AddEvent(500,'
                  'function() return select(4, nxt.InputGetStatus(1)) end,'
                  'function(reactor, datum) return datum == 1 end,'
                  'function() nxt.SoundTone(1230) end)'
                 )
