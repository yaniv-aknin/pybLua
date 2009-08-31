class pybLuaException(Exception):
    pass

class UnexpectedError(pybLuaException):
    def __init__(self, state, payload):
        self.state = state
        self.payload = payload
    def __str__(self):
        return '%s: %s received unexpected %s' % (self.__class__.__name__, self.state, self.payload)
class BadOpcode(UnexpectedError):
    pass
class InternalError(UnexpectedError):
    pass

class pybLuaErrorResponse(pybLuaException):
    def __init__(self, command, error_payload):
        self.command = command
        self.error_payload = error_payload
    def __str__(self):
        return '%s: command %r triggered %s' % (self.__class__.__name__, self.command, self.error_payload,)
class NAKReceived(pybLuaErrorResponse):
    pass
