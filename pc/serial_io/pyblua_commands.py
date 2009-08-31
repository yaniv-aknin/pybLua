class Command(object):
    def __init__(self, result, payload=''):
        self.result = result
        self.payload = payload
    def __str__(self):
        return self.opcode + self.payload
    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.payload)
class Heartbeat(Command):
    opcode = 'H'
class Evaluate(Command):
    opcode = 'E'
