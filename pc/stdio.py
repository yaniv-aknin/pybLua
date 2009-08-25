import os
import tty
import sys
import termios

from twisted.internet import reactor, stdio

from twisted.conch.insults.insults import ServerProtocol
from twisted.conch.manhole import ColoredManhole

class ConsoleManhole(ColoredManhole):
    def connectionLost(self, reason):
        reactor.stop()


def runWithProtocol(cls, reactor=reactor):
    fd = sys.__stdin__.fileno()
    oldSettings = termios.tcgetattr(fd)
    tty.setraw(fd)
    try:
        p = ServerProtocol(cls)
        stdio.StandardIO(p)
        reactor.run()
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, oldSettings)
        os.write(fd, "\r\x1bc\r")
