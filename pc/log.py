import logging

from twisted.python import log

from yalib.logutils import NonBlockingDatagramHandler

def setupLogging(logFile, logLevel):
    if logFile is None:
        handler = NonBlockingDatagramHandler()
        handler.setLevel(logLevel)
        logging.getLogger().setLevel(logLevel)
        logging.getLogger().addHandler(handler)
        # HACK: something is rotten here, and either I don't get it or Twisted is broken; log.PythonLoggingObserver
        #        is an observer, and should have __call__(). Instead it has emit(), which does exactly what we'd
        #        expect from __call__(). So I add a lambda to adapt the two, but still, it is weird.
        log.startLoggingWithObserver(lambda *a, **kw: log.PythonLoggingObserver().emit(*a, **kw), setStdout=False)
    else:
        log.startLogging(file(logFile, 'w'))
