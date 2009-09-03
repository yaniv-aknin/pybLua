from __future__ import print_function
import json
import logging
import os

from twisted.internet import reactor
from twisted.python import log, usage
from twisted.conch.stdio import ConsoleManhole

from yalib.mainutils.usage import executable, BaseExecutable

from log import setupLogging

from controller import Controller
from interact import InteractionManager

@executable
class Interact(BaseExecutable):
    @classmethod
    def initialize_subparser(cls, parser):
        parser.add_argument('-f', '--configuration-file', help='Path to configuration file')
        parser.add_argument('-l', '--log-file', help='Path for logfile')
        parser.add_argument('-L', '--log-level', help='Default loglevel (0-50)', type=int)
        parser.set_defaults(log_level=logging.DEBUG, configuration_file='/etc/pybLua.conf')
    def invoke(self):
        setupLogging(self.options.log_file, self.options.log_level)
        configuration = json.load(file(self.options.configuration_file))
        with InteractionManager() as interactionManager:
            controllers = dict((name, Controller(parameters['usb'], parameters['bluetooth'], interactionManager))
                               for name, parameters in configuration['robots'].items())
            interactionManager.takeControl(ConsoleManhole(self.buildInteractionNamespace(controllers,
                                                                                         interactionManager)))
            for controller in controllers.values():
                controller.startService()
            reactor.run()
    def buildInteractionNamespace(self, controllers, interactionManager):
        # HACK: this function creates a namesapce for the manhole interpreter in a manner that is convenient for
        #        interactive use, it has no value to a non-interactive program
        if len(controllers) == 1:
            firstController = controllers.values()[0]
            return dict(C=firstController, UC=firstController.usb, BC=firstController.bluetooth, I=interactionManager)
        else:
            return dict(C=controllers, I=interactionManager)
