class ProtocolStack(object):
    # HACK: a crude protocol stack which allows a single transport to have several protocols
    #        this does not handle all sorts of cases, like setattr() on the protocol (it will just be set on the
    #        ProtocolStack instance and never be used) or calling connectionLost() upon self.pop()
    __slots__ = ['push', 'pop', '_protocolStack', 'factory']
    def __init__(self, initialProtocol=None):
        self._protocolStack = [initialProtocol] if initialProtocol else []
    def __call__(self):
        return self
    def __getattr__(self, name):
        if not self._protocolStack:
            raise AttributeError('tried gettting an attribute with no concrete protocol')
        return getattr(self._protocolStack[-1], name)
    def __setattr__(self, name, value):
        if name in ('_protocolStack',):
            return super(ProtocolStack, self).__setattr__(name, value)
        if not self._protocolStack:
            raise AttributeError('tried gettting an attribute with no concrete protocol')
        setattr(self._protocolStack[-1], name, value)
    def __repr__(self):
        return '<%s using %r>' % (self.__class__.__name__,
                                  None if not self._protocolStack else self._protocolStack[-1])
    def push(self, protocol):
        self._protocolStack.append(protocol)
    def pop(self):
        return self._protocolStack.pop()

class TerminalBridgeProtocol:
    def __init__(self, transport, keyHandlers=None):
        self.transport = transport
        self.keyHandlers = keyHandlers or {}
    def connectionLost(self, reason):
        pass
    def keystrokeReceived(self, keyID, modifier):
        self.keyHandlers.get(keyID, self.transport.write)(keyID)
