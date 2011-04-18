''' Server-side network routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals 

import logging
from twisted.conch import avatar
from twisted.conch.checkers import SSHPublicKeyDatabase
from twisted.conch.ssh import session, keys, factory, userauth, connection,\
    channel
from twisted.cred import portal
from twisted.internet import reactor
from twisted.spread import pb
from zope.interface import implements

from consys.common import configuration
from consys.common import network

__all__ = ['SSHServer']

_config = configuration.register_section('network',
     {
        'bind-address': 'string(default=0.0.0.0)',
        'port': 'integer(min=1, max=65535, default=2222)',
        'server-key': 'path(default=keys/server)',
        'client-public-key': 'path(default=keys/client.pub)',
        'client-user-name': 'string(default=test)',
     })

_log = logging.getLogger(__name__)

class ClientAvatar(avatar.ConchUser):

    def __init__(self, username):
        avatar.ConchUser.__init__(self)
        self.username = username
        self.channelLookup.update({'session': session.SSHSession})


class ExampleRealm:
    implements(portal.IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        # (implemeted_iface, avatar, logout_callable)
        return interfaces[0], ClientAvatar(avatarId), lambda: None


class InMemoryPublicKeyChecker(SSHPublicKeyDatabase):

    def __init__(self, username, publickey):
        self.username = username
        self.publickey = publickey

    def checkKey(self, credentials):
        return credentials.username == self.username and \
            self.publickey.blob() == credentials.blob
        

class RpcRoot(pb.Root):
    def remote_echo(self, st):
        _log.debug('RPC echoing: "{0}"'.format(st))
        return st


class SSHConnection(connection.SSHConnection):
    '''A server side of the SSH connection.'''
    
    def serviceStarted(self):
        connection.SSHConnection.serviceStarted(self)
        _log.info('Client ready')
        self.rpcRoot = RpcRoot()
        self.rpcFactory = pb.PBServerFactory(self.rpcRoot)
        self.listener = network.SimpleListener(self.rpcFactory)
        self.listener.startListening()
        channel = RpcChannel(listener=self.listener)
        self.openChannel(channel)
        
    def serviceStopped(self):
        self.listener.stopListening()
        connection.SSHConnection.serviceStopped(self)
        

class RpcChannel(channel.SSHChannel):
    name = network.RPC_CHANNEL_NAME

    def __init__(self, listener, localWindow = 0, localMaxPacket = 0,
                       remoteWindow = 0, remoteMaxPacket = 0,
                       conn = None, data=None, avatar = None):
        channel.SSHChannel.__init__(self, localWindow, localMaxPacket,
                                    remoteWindow, remoteMaxPacket, conn,
                                    data, avatar)
        self.listener = listener

    def openFailed(self, reason):
        _log.error('RPC channel opening failed: {0}'.format(reason))
    
    def channelOpen(self, extraData):
        _log.info('RPC channel opened')
        self.protocol = self.listener.makeConnection(self)
        
    def dataReceived(self, data):
        self.protocol.dataReceived(data)
            

class SSHServerFactory(factory.SSHFactory):
    publicKeys = {
        b'ssh-rsa': keys.Key.fromFile(_config['server-key']).public()
    }
    privateKeys = {
        b'ssh-rsa': keys.Key.fromFile(_config['server-key'])
    }
    services = {
        b'ssh-userauth': userauth.SSHUserAuthServer,
        b'ssh-connection': SSHConnection
    }

portal = portal.Portal(ExampleRealm())
portal.registerChecker(
    InMemoryPublicKeyChecker(_config['client-user-name'],
                             keys.Key.fromFile(_config['client-public-key'])))
SSHServerFactory.portal = portal

def start_networking():
    reactor.listenTCP(_config['port'], SSHServerFactory(), 
                      interface=_config['bind-address'])

dispatch_loop = network.dispatch_loop
