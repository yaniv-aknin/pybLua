from twisted.python import log

from ..base import State

from protocol import pbLuaConsoleProtocol
from errors import UnexpectedOutput


PROMPTS = ('>', '>>')

def isPromptPrefixed(line):
    return line.startswith(PROMPTS)
def isPrompt(line):
    return line.strip() in PROMPTS

class pbLuaState(State):
    class __metaclass__(type):
        def __init__(cls, name, bases, env):
            pbLuaConsoleProtocol.knownStates.append(cls)
        def __str__(cls):
            return cls.__name__

class pbLuaInitializing(pbLuaState):
    def enter(self, previousState):
        pbLuaState.enter(self, previousState)
        self.attempts = 0
        self.sendNewLineToGetPrompt()
    def sendNewLineToGetPrompt(self):
        self.parent.transport.write('\n')
        self.attempts += 1
    def lineReceived(self, line):
        if isPrompt(line):
            self.parent.setState(pbLuaConnected)
        else:
            if self.attempts > 1:
                log.msg('desired prompt, received %r instead' % (line,))
            if self.attempts < 2:
                self.sendNewLineToGetPrompt()
            else:
                log.err(UnexpectedOutput('unable to get prompt'))

class pbLuaConnected(pbLuaState):
    pass

class pbLuaLoading(pbLuaState):
    enterFrom=(pbLuaConnected,)
    def enter(self, previousState, lines, autoExecute=True):
        pbLuaState.enter(self, previousState)
        self.lines = lines
        self.nextState = pbLuaRunning if autoExecute else pbLuaConnected
        self.sendLine()
    def sendLine(self):
        line = self.lines.pop(0)
        log.msg('sent: ' + line)
        self.parent.transport.write(line + '\n')
    def lineReceived(self, line):
        if not isPromptPrefixed(line):
            log.err(UnexpectedOutput('unexpected: %s' % (line,)))
            self.parent.setState(pbLuaConnected)
        else:
            if self.lines:
                self.sendLine()
            else:
                self.parent.setState(self.nextState)

class pbLuaTerminal(pbLuaState):
    enterFrom=(pbLuaConnected, pbLuaInitializing)
    def enter(self, previousState, stdio):
        pbLuaState.enter(self, previousState)
        self.parent.setRawMode()
        self.stdio = stdio
    def dataReceived(self, data):
        self.stdio.write(data)
    def exit(self, nextState):
        self.parent.setLineMode()

class pbLuaRunning(pbLuaState):
    enterFrom=(pbLuaConnected, pbLuaLoading)
    def enter(self, previousState):
        pbLuaState.enter(self, previousState)
        self.parent.transport.write('LoaderExecute()\n\n')
    def lineReceived(self, line):
        if isPrompt(line):
            self.parent.setState(pbLuaConnected)
        elif not isPromptPrefixed(line):
            pbLuaState.lineReceived(self, line)
