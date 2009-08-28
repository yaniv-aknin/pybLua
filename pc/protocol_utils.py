class ProtocolSwitcher:
    def __init__(self, initialProtocol=None):
        self._protocol = initialProtocol
    def __call__(self):
        return self
    def __getattr__(self, attribute_name):
        if self._protocol is None:
            raise AttributeError('tried gettting an attribute with no concrete protocol')
        return getattr(self._protocol, attribute_name)
    def makeConnection(self, transport):
        assert self._protocol is not None, 'can not makeConnection with no concrete protocol'
        try:
            factory = self.factory
        except AttributeError:
            pass
        else:
            self._protocol.factory = factory
        self._protocol.makeConnection(transport)
    def switch(self, protocol):
        self._protocol = protocol
