class StateException(Exception):
    pass
class UnexpectedOutput(StateException):
    pass
class InvalidTransition(StateException):
    pass
