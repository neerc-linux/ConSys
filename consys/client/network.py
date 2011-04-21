''' Client-side network routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals 

import os
import logging

from twisted.conch.ssh import transport, userauth, connection, keys, channel
from twisted.internet import defer, protocol, reactor
from twisted.spread import pb

from consys.common import configuration
from consys.common import network
from twisted.conch import error

_config = configuration.register_section('network', 
    {
        'server-address': 'string()',
        'port': 'integer(min=1, max=65535, default=2222)',
        'client-key': 'path(default=keys/client)',
        'server-public-key': 'path(default=keys/server.pub)',
        'client-user-name': 'string(default=terminal)',
    })

_log = logging.getLogger(__name__)

class ClientTransport(transport.SSHClientTransport):
    ''' '''
    def __init__(self, knownHostKey):
        self.knownHostKey = knownHostKey
    
    def verifyHostKey(self, hostKey, fingerprint):
        if hostKey != self.knownHostKey.blob():
            _log.warning('invalid host key fingerprint:'
                         ' {0}'.format(fingerprint))
            return defer.fail(error.ConchError('Invalid host key'))
        _log.info('valid host key fingerprint: {0}'.format(fingerprint))
        return defer.succeed(True) 

    def connectionSecure(self):
        username = _config['client-user-name'].encode('utf-8')
        self.requestService(SimplePubkeyUserAuth(username, SSHConnection()))


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
    def serviceStarted(self):
        connection.SSHConnection.serviceStarted(self)
        _log.info('Authentication successful')
        self.rpcFactory = pb.PBClientFactory()
        rpcRoot = self.rpcFactory.getRootObject()
        rpcRoot.addCallback(self.initRpc)
        
    def channel_rpc_consys(self, windowSize, maxPacket, data):
        channel = RpcChannel(factory=self.rpcFactory, remoteWindow=windowSize,
                             remoteMaxPacket=maxPacket, data=data)
        return channel
    
    def initRpc(self, root):
        self.rpcRoot = root
        _log.info('RPC ready')
        _log.debug('Calling test method')
        self.rpcRoot.callRemote(b'echo', '566: test').addCallback(self._cbInit)
        
    def _cbInit(self, result):
        _log.debug('Got result: "{0}"'.format(result))


class RpcChannel(channel.SSHChannel):
    name = network.RPC_CHANNEL_NAME

    def __init__(self, factory, localWindow = 0, localMaxPacket = 0,
                       remoteWindow = 0, remoteMaxPacket = 0,
                       conn = None, data=None, avatar = None):
        channel.SSHChannel.__init__(self, localWindow, localMaxPacket,
                                    remoteWindow, remoteMaxPacket, conn,
                                    data, avatar)
        self.factory = factory

    def openFailed(self, reason):
        _log.error('RPC channel opening failed: {0}'.format(reason))
    
    def channelOpen(self, extraData):
        _log.info('RPC channel opened')
        self.protocol = network.connectSSH(self, self.factory)
        
    def failIfNotConnected(self, err):
        _log.error('Could not connect to the RPC server')
        self.loseConnection()

    def dataReceived(self, data):
        self.protocol.dataReceived(data)

_server_public_key = keys.Key.fromFile(_config['server-public-key'])

def start_networking():
    creator = protocol.ClientCreator(reactor, ClientTransport,
                                     _server_public_key)
    creator.connectTCP(_config['server-address'], _config['port'])

dispatch_loop = network.dispatch_loop
