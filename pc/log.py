import logging.handlers
import logging
import socket

from twisted.python import log

class NonBlockingDatagramHandler(logging.handlers.DatagramHandler):
    "Mostly the vanilla DatagramHandler with some extra safety/non-blockingess additions"
    def __init__(self, host='127.0.0.1', port=logging.handlers.DEFAULT_UDP_LOGGING_PORT):
        logging.handlers.DatagramHandler.__init__(self, host, port)

    def makeSocket(self):
        "The DatagramHandler factory is overriden to create a non-blocking socket."
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        return sock

    def send(self, s):
        """
        Add exception handling. I've read the CPython code of sendto and am not sure it can create an exception
         on a nonblocking datagram socket, but better safe than sorry.
        """
        if self.sock is None:
            self.createSocket()
        try:
            self.sock.sendto(s, (self.host, self.port))
        except socket.error:
            self.sock.close()
            # Note: so we can call createSocket next time
            self.sock = None

def setupLogging(logFile=None):
    if logFile is None:
        handler = NonBlockingDatagramHandler()
        handler.setLevel(10)
        logging.getLogger().setLevel(10)
        logging.getLogger().addHandler(handler)
        # HACK: something is rotten here, and either I don't get it or Twisted is broken; log.PythonLoggingObserver
        #        is an observer, and should have __call__(). Instead it has emit(), which does exactly what we'd
        #        expect from __call__(). So I add a lambda to adapt the two, but still, it is weird.
        log.startLoggingWithObserver(lambda *a, **kw: log.PythonLoggingObserver().emit(*a, **kw), setStdout=False)
    else:
        log.startLogging(file(logFile, 'w'))
