''' Admin-side network routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals 

import random

from twisted.conch import error
from twisted.conch.ssh import transport, userauth, connection, keys
from twisted.internet import defer, reactor, protocol, endpoints

from consys.common import log
from consys.common import configuration, app
from consys.common import auto

_config = configuration.register_section('network', 
    {
        'server-public-key': 'path(default=keys/server.pub)',
    })

_log = log.getLogger(__name__)


class Credentials(object):
    ''' Simple username/password credentials. '''
    def __init__(self, username, password):
        self.username = username
        self.password = password


class ClientTransport(transport.SSHClientTransport):
    ''' An initial SSH transport, responsible for the encryption. '''
    def __init__(self, knownHostKey, deferred, onDisconnect, cred):
        self.knownHostKey = knownHostKey
        self.deferred = deferred
        self.onDisconnect = onDisconnect
        self.cred = cred
    
    def verifyHostKey(self, hostKey, fingerprint):
        if hostKey != self.knownHostKey.blob():
            _log.warning('invalid host key fingerprint:'
                         ' {0}'.format(fingerprint))
            return defer.fail(error.ConchError('Invalid host key'))
        _log.info('valid host key fingerprint: {0}'.format(fingerprint))
        return defer.succeed(True) 

    def connectionSecure(self):
        username = self.cred.username.encode('utf-8')
        password = self.cred.password.encode('utf-8')
        connection = SSHConnection(self.deferred, self.onDisconnect)
        self.requestService(SimplePasswordUserAuth(username, connection,
                                                   password))

    def connectionLost(self, reason):
        transport.SSHClientTransport.connectionLost(self, reason)
        if not self.deferred.called:
            self.deferred.errback(reason)
        

class SimplePasswordUserAuth(userauth.SSHUserAuthClient):

    preferredOrder = [b'password']
    
    def __init__(self, user, instance, password):
        userauth.SSHUserAuthClient.__init__(self, user, instance)
        self.password = password
        self.used = False
    
    def getPassword(self, prompt=None):
        if self.used:
            return None
        self.used = True
        return defer.succeed(self.password)
    

class SSHConnection(connection.SSHConnection):
    def __init__(self, deferred, onDisconnect):
        connection.SSHConnection.__init__(self)
        self.deferred = deferred
        self.onDisconnect = onDisconnect
    
    def serviceStarted(self):
        connection.SSHConnection.serviceStarted(self)
        _log.info('Authentication successful')
        self.deferred.callback(None)
        
    def serviceStopped(self):
        self.onDisconnect()
        connection.SSHConnection.serviceStopped(self)
                

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
    
    def __init__(self):
        auto.SimpleAutomaton.__init__(self)
        self.connection = None
        self.deferred = None
        self.server_string = None
        self.credentials = None
        self.signal_error = False
        self.delay = self.initial_delay
        
    def doConnect(self):
        if self.connection is not None:
            self.disconnect()
        self.deferred = defer.Deferred()
        def _cbConnectionLost():
            self.event('connectionLost')
        f = protocol.Factory()
        f.protocol = lambda: ClientTransport(_server_public_key, self.deferred,
                                             _cbConnectionLost,
                                             self.credentials)
        endpoint = endpoints.clientFromString(reactor, self.server_string)
        d = endpoint.connect(f)
        d.addErrback(self.deferred.errback)
        def _cbConnection(rv):
            self.event('connected')
            self.signal_error = False
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

_server_public_key = keys.Key.fromFile(_config['server-public-key'])

autoConnection = ConnectionAutomaton()

def do_connect(server_string, credentials):
    autoConnection.event('disconnect')
    autoConnection.server_string = server_string
    autoConnection.credentials = credentials
    autoConnection.signal_error = True
    autoConnection.event('connect')
    def _ebFailed(failure):
        autoConnection.event('disconnect')
        _log.warning('Connection failed')
        return failure
    return autoConnection.deferred.addErrback(_ebFailed)

def on_shutdown():
    autoConnection.event('disconnect')

app.shutdown.connect(on_shutdown)
