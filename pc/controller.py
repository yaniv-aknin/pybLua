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
from stdio import TerminalBridgeProtocol
from recipe import loadRecipeLines

class Controller(MultiService):
    def __init__(self, options, stdio):
        MultiService.__init__(self)
        self.options = options
        self.usb = USBController(options.opts['usb'])
        self.usb.setServiceParent(self)
        self.bluetooth = BluetoothController(options.opts['bluetooth'])
        self.stdio = stdio
    def startService(self):
        MultiService.startService(self)
        if self.options.opts['terminal']:
            self.terminal()
    def load(self, path='master.recipe'):
        from lego import PROJECT_ROOT
        if os.path.isfile(os.path.join(PROJECT_ROOT, 'nxt', path)):
            path = (os.path.join(PROJECT_ROOT, 'nxt', path))
        self.usb.setState(pbLuaLoading, loadRecipeLines(path))
    def terminal(self):
        self.stdio.protocolStack.push(TerminalBridgeProtocol(self.usb.port, {CTRL_D: self.manhole}))
        self.usb.setState(pbLuaTerminal, self.stdio.stdio)
    def manhole(self, keyID):
        self.stdio.protocolStack.pop()
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
