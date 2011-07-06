''' Common network routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals 

import random

from twisted.conch.ssh import channel, transport
from twisted.internet import defer, endpoints, reactor, error
from twisted.python.failure import Failure

from consys.common import log, auto

_log = log.getLogger(__name__)

class InvalidHostKey(Exception):
    def __init__(self, host, offendingKey, validKey):
        Exception.__init__(self, host, offendingKey, validKey)
        self.host = host
        self.offendingKey = offendingKey
        self.validKey = validKey

    def __str__(self):
        return "Invalid host key '{0}', expecting that '{1}' has " \
            "host key '{2}'".format(self.offendingKey, self.host, self.validKey)


class SSHClientTransport(transport.SSHClientTransport):
    ''' An initial SSH transport, responsible for the encryption. '''
    def __init__(self, knownHostKey, deferred, onDisconnect, connectionFactory):
        self.knownHostKey = knownHostKey
        self.deferred = deferred
        self.onDisconnect = onDisconnect
        self.connectionFactory = connectionFactory
        self.authenticator = None

    def verifyHostKey(self, hostKey, fingerprint):
        if hostKey != self.knownHostKey.blob():
            host = self.transport.getPeer()
            _log.warning('invalid host key fingerprint:'
                         ' {0}'.format(fingerprint))
            validFingerprint = self.knownHostKey.fingerprint()
            self.failure = Failure(InvalidHostKey(host, fingerprint,
                                                     validFingerprint))
            return defer.fail(self.failure)
        _log.info('valid host key fingerprint: {0}'.format(fingerprint))
        return defer.succeed(True)

    def getAuthenticator(self, connection):
        ''' To be overridden in subclasses. '''
        return None

    def connectionSecure(self):
        connection = self.connectionFactory(self.deferred, self.onDisconnect)
        self.authenticator = self.getAuthenticator(connection)
        self.requestService(self.authenticator)

    def connectionLost(self, reason):
        transport.SSHClientTransport.connectionLost(self, reason)
        if not self.deferred.called:
            if reason.check(error.ConnectionDone):
                if self.authenticator:
                    if self.authenticator.failure:
                        reason = self.authenticator.failure
                elif self.failure:
                    reason = self.failure
            self.deferred.errback(reason)


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
                    ('connecting', 'connectionLost'): ('cooldown',
                                                       ['cooldown']),
                    ('connecting', 'disconnect'): ('cancelled', []),
                    ('cancelled', 'disconnect'): ('cancelled', []),
                    ('cancelled', 'connected'): ('disconnected',
                                                 ['connected', 'disconnect']), 
                    ('cancelled', 'connectionLost'): ('disconnected', []),
                    ('cooldown', 'timer'): ('connecting', ['doConnect']), 
                    ('cooldown', 'connectionLost'): ('cooldown', []),
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
            self.event('connectionLost')
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

