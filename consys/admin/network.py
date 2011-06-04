''' Admin-side network routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals 

from twisted.conch import error
from twisted.conch.ssh import transport, userauth, connection, keys
from twisted.internet import defer, reactor, protocol

from consys.common import log, network
from consys.common import configuration, app

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
                


def _cbConnectionLost():
    autoConnection.event('connectionLost')

_credentials = None
_client_factory = protocol.Factory()
_client_factory.protocol = lambda: ClientTransport(_server_public_key, 
                                                   autoConnection.deferred,
                                                   _cbConnectionLost,
                                                   _credentials)

_server_public_key = keys.Key.fromFile(_config['server-public-key'])

autoConnection = network.ConnectionAutomaton(_client_factory)

def do_connect(server_string, credentials):
    autoConnection.event('disconnect')
    autoConnection.server_string = server_string
    global _credentials
    _credentials = credentials
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
