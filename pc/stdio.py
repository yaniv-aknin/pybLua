import os
import tty
import sys
import termios

from zope.interface import implements

from twisted.internet import reactor, stdio
from twisted.application.service import Service
from twisted.conch.insults.insults import ServerProtocol
from twisted.conch.stdio import ConsoleManhole

class StdIOController(Service):
    def __init__(self, manholeFactory):
        self.manholeFactory = manholeFactory
        self.fd = None
        self.oldSettings = None
    def startService(self):
        self.fd = sys.__stdin__.fileno()
        self.oldSettings = termios.tcgetattr(self.fd)
        tty.setraw(self.fd)
        stdio.StandardIO(ServerProtocol(self.manholeFactory))
    def stopService(self):
        termios.tcsetattr(self.fd, termios.TCSANOW, self.oldSettings)
        os.write(self.fd, "\r\x1bc\r")
        self.fd = None
        self.oldSettings = None
