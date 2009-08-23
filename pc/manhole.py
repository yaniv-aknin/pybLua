# Copyright (c) 2001-2007 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Asynchronous local terminal input handling

@author: Jp Calderone
"""

import os, tty, sys, termios

from twisted.internet import reactor, stdio, protocol, defer
from twisted.python import failure, reflect, log

from twisted.conch.insults.insults import ServerProtocol
from twisted.conch.manhole import ColoredManhole

class UnexpectedOutputError(Exception):
    pass


class ConsoleManhole(ColoredManhole):
    """
    A manhole protocol specifically for use with L{stdio.StandardIO}.
    """
    def connectionLost(self, reason):
        """
        When the connection is lost, there is nothing more to do.  Stop the
        reactor so that the process can exit.
        """
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
