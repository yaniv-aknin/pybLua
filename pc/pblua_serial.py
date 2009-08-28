from functools import partial

from twisted.protocols.basic import LineOnlyReceiver
from twisted.python import log

class UnexpectedOutput(Exception):
    pass
class InvalidTransition(Exception):
    pass

PROMPTS = ('>', '>>')

def isPromptPrefixed(line):
    return line.startswith(PROMPTS)
def isPrompt(line):
    return line.strip() in PROMPTS

class pbLuaSerialProtocol(LineOnlyReceiver):
    knownStates = []
    def __init__(self, parent):
        self.parent = parent
        self.states = dict((cls, cls(self)) for cls in self.knownStates)
        self.state = None
        self.outgoing = []
    def setState(self, state):
        if state.enterFrom and self.state.__class__ not in state.enterFrom:
            raise InvalidTransition('invalid state change: %s -> %s' % (self.state, state))
        log.msg('state: %s -> %s' % (self.state, state))
        if self.state is not None:
            self.state.exit()
        previousState = self.state
        self.state = self.states[state]
        self.state.enter(previousState)
    def connectionMade(self):
        self.setState(pbLuaInitializing)
    def lineReceived(self, line):
        return self.state.lineReceived(line)
    def connectionLost(self, reason):
        return self.state.connectionLost(reason)

class pbLuaState:
    enterFrom = tuple()
    class __metaclass__(type):
        def __init__(cls, name, bases, env):
            pbLuaSerialProtocol.knownStates.append(cls)
        def __str__(cls):
            return cls.__name__
    def __init__(self, parent):
        self.parent = parent
        self.transport = parent.transport
    def __str__(self):
        return self.__class__.__name__
    def enter(self, previousState):
        pass
    def exit(self):
        pass
    def connectionMade(self):
        pass
    def lineReceived(self, line):
        pass
    def connectionLost(self, reason):
        pass

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
    def connectionLost(self, reason):
        log.msg('init connection lost: %s' % (reason,))

class pbLuaConnected(pbLuaState):
    def lineReceived(self, line):
        log.msg('received: ' + line.strip())
    def connectionLost(self, reason):
        log.msg('connected connection lost: %s' % (reason,))

class pbLuaLoading(pbLuaState):
    enterFrom=(pbLuaConnected,)
    def enter(self, previousState):
        pbLuaState.enter(self, previousState)
        self.sendLine()
    def sendLine(self):
        line = self.parent.outgoing.pop(0)
        log.msg('sent: ' + line)
        self.parent.transport.write(line + '\n')
    def lineReceived(self, line):
        if not isPromptPrefixed(line):
            log.err(UnexpectedOutput('unexpected: %s' % (line,)))
            self.parent.setState(pbLuaConnected)
        else:
            if self.parent.outgoing:
                self.sendLine()
            else:
                self.parent.setState(pbLuaConnected)
    def connectionLost(self, reason):
        log.msg('loading connection lost: %s' % (reason,))

class pbLuaTerminal(pbLuaState):
    enterFrom=(pbLuaConnected,)
