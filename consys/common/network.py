''' Common network routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals 

import random

from twisted.conch.ssh import channel
from twisted.internet import defer, endpoints, reactor

from consys.common import log, auto

_log = log.getLogger(__name__)

class ProtocolChannel(channel.SSHChannel):
    ''' General channel for running protocols over SSH. '''
    def __init__(self, factory, localWindow = 0, localMaxPacket = 0,
                       remoteWindow = 0, remoteMaxPacket = 0,
                       conn = None, data=None, avatar = None):
        channel.SSHChannel.__init__(self, localWindow, localMaxPacket,
                                    remoteWindow, remoteMaxPacket, conn,
                                    data, avatar)
        self.factory = factory
        self.deferred = defer.Deferred()

    def openFailed(self, reason):
        self.deferred.errback(reason)
    
    def channelOpen(self, extraData):
        self.protocol = self.factory.buildProtocol(None)
        self.protocol.makeConnection(self)
        self.deferred.callback(self)

    def dataReceived(self, data):
        self.protocol.dataReceived(data)
        
    # TODO: Add new IAddress implementation for SSH channels
    def getPeer(self):
        return 'SSH:{0}'.format(self.conn.transport.transport.getPeer())

    def getHost(self):
        return 'SSH:{0}'.format(self.conn.transport.transport.getHost())

RPC_CHANNEL_NAME = b'rpc@consys'

class RpcChannel(ProtocolChannel):
    name = RPC_CHANNEL_NAME

    def openFailed(self, reason):
        ProtocolChannel.openFailed(self, reason)
        _log.error('RPC channel opening failed: {0}'.format(reason))
    
    def channelOpen(self, extraData):
        ProtocolChannel.channelOpen(self, extraData)
        _log.info('RPC channel opened')

AMP_CHANNEL_NAME = b'amp@consys'

class AmpChannel(ProtocolChannel):
    name = AMP_CHANNEL_NAME

    def openFailed(self, reason):
        ProtocolChannel.openFailed(self, reason)
        _log.error('AMP channel opening failed: {0}'.format(reason))
    
    def channelOpen(self, extraData):
        ProtocolChannel.channelOpen(self, extraData)
        _log.info('AMP channel opened')


class ConnectionAutomaton(auto.SimpleAutomaton):
    _states = ['disconnected', 'connecting', 'cooldown', 'connected', 
               'cancelled']
    _start_state = 'disconnected'
    _transitions = {
                    ('disconnected', 'connect'): ('connecting', ['doConnect']),
                    ('disconnected', 'disconnect'): ('disconnected', []),
                    ('disconnected', 'connectionLost'): ('disconnected', []),
                    ('connecting', 'connected'): ('connected', ['connected']), 
                    ('connecting', 'connectionFailed'): ('cooldown', 
                                                         ['cooldown']), 
                    ('connecting', 'disconnect'): ('cancelled', []), 
                    ('cancelled', 'disconnect'): ('cancelled', []),
                    ('cancelled', 'connected'): ('disconnected', 
                                                 ['connected', 'disconnect']), 
                    ('cancelled', 'connectionFailed'): ('disconnected', []), 
                    ('cancelled', 'connectionLost'): ('disconnected', []),
                    ('cooldown', 'timer'): ('connecting', ['doConnect']), 
                    ('cooldown', 'disconnect'): ('disconnected',
                                                 ['cancelTimer']), 
                    ('connected', 'connectionLost'): ('connecting',
                                                      ['doConnect']),
                    ('connected', 'disconnect'): ('disconnected',
                                                  ['disconnect']), 
                }
    initial_delay = 1.0 # seconds
    factor = 1.72
    max_delay = 15.0 # seconds
    jitter = 0.12
    
    def __init__(self, factory):
        auto.SimpleAutomaton.__init__(self)
        self.connection = None
        self.deferred = None
        self.server_string = None
        self.signal_error = False
        self.delay = self.initial_delay
        self.factory = factory
        
    def doConnect(self):
        if self.connection is not None:
            self.disconnect()
        self.deferred = defer.Deferred()
        endpoint = endpoints.clientFromString(reactor, self.server_string)
        d = endpoint.connect(self.factory)
        d.addErrback(self.deferred.errback)
        def _cbConnection(rv):
            self.event('connected')
            self.signal_error = False
            return rv
        def _ebConnection(failure):
            self.event('connectionFailed')
            if self.signal_error:
                self.signal_error = False
                return failure
        self.deferred.addCallbacks(_cbConnection, _ebConnection)
    
    def connected(self):
        self.delay = self.initial_delay
        self.connection = self.deferred.result
    
    def cooldown(self):
        def _cbTimer():
            self.event('timer')
        self.delay = min(self.delay * self.factor, self.max_delay)
        if self.jitter:
            self.delay = random.normalvariate(self.delay,
                                              self.delay * self.jitter)
        self.timer = reactor.callLater(self.delay, _cbTimer)
    
    def disconnect(self):
        if self.connection is not None:
            self.connection.transport.loseConnection()
            self.connection = None        
    
    def cancelTimer(self):
        self.timer.cancel()

