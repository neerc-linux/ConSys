''' Client-side network routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals 

import os
import random

from twisted.conch import error
from twisted.conch.ssh import transport, userauth, connection, keys
from twisted.internet import defer, reactor, protocol, endpoints
from twisted.spread import pb

from consys.common import log
from consys.common import configuration, app
from consys.common import network
from consys.common import auto
from consys.client import root

_config = configuration.register_section('network', 
    {
        'server-string': 'string()',
        'client-key': 'path(default=keys/client)',
        'server-public-key': 'path(default=keys/server.pub)',
        'client-user-name': 'string(default=terminal)',
    })

_log = log.getLogger(__name__)

class ClientTransport(transport.SSHClientTransport):
    ''' '''
    def __init__(self, knownHostKey, deferred, onDisconnect):
        self.knownHostKey = knownHostKey
        self.deferred = deferred
        self.onDisconnect = onDisconnect
    
    def verifyHostKey(self, hostKey, fingerprint):
        if hostKey != self.knownHostKey.blob():
            _log.warning('invalid host key fingerprint:'
                         ' {0}'.format(fingerprint))
            return defer.fail(error.ConchError('Invalid host key'))
        _log.info('valid host key fingerprint: {0}'.format(fingerprint))
        return defer.succeed(True) 

    def connectionSecure(self):
        username = _config['client-user-name'].encode('utf-8')
        connection = SSHConnection(self.deferred, self.onDisconnect)
        self.requestService(SimplePubkeyUserAuth(username, connection))


class SimplePubkeyUserAuth(userauth.SSHUserAuthClient):
    
    preferredOrder = [b'publickey']
                
    def getPublicKey(self):
        path = _config['client-key']
        if not os.path.exists(path) or self.lastPublicKey:
            return
        # public blob of a private key
        key = keys.Key.fromFile(path)
        return key.public()

    def getPrivateKey(self):
        path = _config['client-key']
        return defer.succeed(keys.Key.fromFile(path))
    

class SSHConnection(connection.SSHConnection):
    def __init__(self, deferred, onDisconnect):
        connection.SSHConnection.__init__(self)
        self.deferred = deferred
        self.onDisconnect = onDisconnect
    
    def serviceStarted(self):
        connection.SSHConnection.serviceStarted(self)
        _log.info('Authentication successful')
        self.mind = root.Root()
        self.rpcFactory = pb.PBClientFactory()
        rpcRoot = self.rpcFactory.getRootObject()
        rpcRoot.addCallback(self.initRpc)
        rpcRoot.addErrback(self.deferred.errback)
        
    def serviceStopped(self):
        self.onDisconnect()
        self.rpcFactory.disconnect()
        connection.SSHConnection.serviceStopped(self)
        
    def channel_rpc_consys(self, windowSize, maxPacket, data):
        channel = network.RpcChannel(factory=self.rpcFactory,
                                     remoteWindow=windowSize,
                                     remoteMaxPacket=maxPacket, data=data)
        return channel
    
    def initRpc(self, rpcRoot):
        self.rpcRoot = rpcRoot
        d = self.rpcRoot.callRemote(b'set_mind', self.mind)
        d.addCallback(self._cbInitRpc)
        d.chainDeferred(self.deferred)
        
    def _cbInitRpc(self, result):
        _log.info('RPC ready')
        return self
        

def _cbConnectionLost():
    autoConnection.event('connectionLost')

_client_factory = protocol.Factory()
_client_factory.protocol = lambda: ClientTransport(_server_public_key,
                                                   autoConnection.deferred,
                                                   _cbConnectionLost)

_server_public_key = keys.Key.fromFile(_config['server-public-key'])

autoConnection = network.ConnectionAutomaton(_client_factory)
autoConnection.server_string = _config['server-string']

def on_startup():
    autoConnection.event('connect')

def on_shutdown():
    autoConnection.event('disconnect')

app.startup.connect(on_startup)
app.shutdown.connect(on_shutdown)
