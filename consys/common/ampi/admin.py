'''
AMP admin commands.
@author: Nikita Ofitserov
'''
from twisted.protocols import amp

class NoSuchObjectError(Exception):
    pass

class TerminalOfflineError(Exception):
    pass

# Common commands

class Ping(amp.Command):
    arguments = []
    response = []
    
# Admin -> Server commands

class GetTerminals(amp.Command):
    arguments = []
    response = [(b'ids', amp.ListOf(amp.Integer()))]
    
class GetTerminalData(amp.Command):
    arguments = [(b'id', amp.Integer())]
    response = [(b'name', amp.String()),
                (b'online', amp.Boolean())]
    errors = {NoSuchObjectError: "NO_SUCH_OBJECT"}

class ShutdownTerminal(amp.Command):
    arguments = [(b'id', amp.Integer())]
    response = []
    errors = {NoSuchObjectError: "NO_SUCH_OBJECT",
              TerminalOfflineError: "TERMINAL_OFFLINE"}
    
# Server -> Admin commands

class NewTerminal(amp.Command):
    arguments = [(b'id', amp.Integer())]
    response = []
    requiresAnswer = False
    
class RemovedTerminal(amp.Command):
    arguments = [(b'id', amp.Integer())]
    response = []
    requiresAnswer = False
    
class TerminalStatusUpdated(amp.Command):
    arguments = [(b'id', amp.Integer()), (b'online', amp.Boolean())]
    response = []
    requiresAnswer = False

    