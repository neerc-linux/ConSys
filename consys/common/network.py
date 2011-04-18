''' Common network routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals 

import logging

from twisted.internet import reactor, base, defer
from twisted.python import log as twisted_log

_log = logging.getLogger(__name__)

_log_observer =  twisted_log.PythonLoggingObserver()
_log_observer.start()


RPC_CHANNEL_NAME = b'rpc@consys'


def dispatch_loop():
    '''Dispatches messages until program shutdown.'''
    reactor.run()


class SimpleConnector(base.BaseConnector):
    def __init__(self, transport, factory, timeout, reactor=None):
        self.transport = transport
        base.BaseConnector.__init__(self, factory, timeout, reactor)

    def _makeTransport(self):
        return self.transport


class SimpleListener(object):
    def __init__(self, factory, reactor=None):
        self.factory = factory
        self.listening = False

    def startListening(self):
        self.factory.doStart()
        self.listening = True

    def stopListening(self):
        self.listening = False
        self.factory.doStop()
        return defer.succeed(True)
    
    def makeConnection(self, transport):
        protocol = self.factory.buildProtocol(None)
        if protocol is None:
            return
        protocol.makeConnection(transport)
        return protocol
        

def connectSSH(channel, factory, timeout=30):
    c = SimpleConnector(channel, factory, timeout, reactor)
    c.connect()
    protocol = c.buildProtocol(None)
    protocol.makeConnection(channel)
    return protocol

