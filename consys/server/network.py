''' Server-side network routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals

import base64
import hashlib
import logging

from zope.interface import implements
from twisted.conch import avatar
from twisted.conch.checkers import SSHPublicKeyDatabase
from twisted.conch.manhole_ssh import TerminalSession
from twisted.conch.ssh import session, keys, factory, userauth, connection, \
    channel
from twisted.cred import portal
from twisted.cred.checkers import FilePasswordDB
from twisted.internet import reactor
from twisted.python import components
from twisted.spread import pb

from consys.common import configuration, network
from twisted.conch.manhole_tap import chainedProtocolFactory
from twisted.conch.insults import insults
from twisted.conch.manhole import ColoredManhole


__all__ = ['SSHServer']

_config = configuration.register_section('network',
     {
        'bind-address': 'string(default=0.0.0.0)',
        'port': 'integer(min=1, max=65535, default=2222)',
        'server-key': 'path(default=keys/server)',
        'client-public-key': 'path(default=keys/client.pub)',
        'client-user-name': 'string(default=terminal)',
        'user-auth-db': 'path(default=data/admins.txt)'
     })

_log = logging.getLogger(__name__)

class ClientAvatar(avatar.ConchUser):

    def __init__(self, terminalId):
        avatar.ConchUser.__init__(self)
        self.terminalId = terminalId
        self.channelLookup.update({'session': session.SSHSession})
        self.rpcRoot = RpcRoot()
        self.rpcFactory = pb.PBServerFactory(self.rpcRoot)
        self.listener = network.SimpleListener(self.rpcFactory)

    def login(self, connection):
        self.connection = connection
        self.listener.startListening()
        channel = RpcChannel(listener=self.listener)
        self.connection.openChannel(channel)
    
    def logout(self):
        self.listener.stopListening()
        

class AdminAvatar(avatar.ConchUser):

    def __init__(self, username):
        avatar.ConchUser.__init__(self)
        self.username = username
        self.namespace = {"avatar": self}
        self.channelLookup.update({'session': session.SSHSession})

    def login(self, connection):
        pass
    
    def logout(self):
        pass


class AdminTerminalSession(TerminalSession):
    chainedProtocolFactory = lambda self: \
        insults.ServerProtocol(ColoredManhole, self.original.namespace)
    

components.registerAdapter(AdminTerminalSession, AdminAvatar, session.ISession)


class ExampleRealm:
    implements(portal.IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        if avatarId == _config['client-user-name']:
            # FIXME: ask the client's ID 
            avatar = ClientAvatar('no-id')
        else:
            avatar = AdminAvatar(avatarId)
        # (implemeted_iface, avatar, logout_callable)
        return interfaces[0], avatar, avatar.logout


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
        _log.info('SSH connection ready')
        self.transport.avatar.login(self)
        
    def serviceStopped(self):
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

def _htpasswd_hash(username, password, hashedpassword):
    if hashedpassword.startswith('{SHA}'):
        return '{SHA}' + base64.b64encode(hashlib.sha1(password).digest())
    return 'bad-hash-algorithm'

portal = portal.Portal(ExampleRealm())
portal.registerChecker(FilePasswordDB(_config['user-auth-db'],
                                      hash=_htpasswd_hash, cache=True))
portal.registerChecker(
    InMemoryPublicKeyChecker(_config['client-user-name'],
                             keys.Key.fromFile(_config['client-public-key'])))
SSHServerFactory.portal = portal

def start_networking():
    reactor.listenTCP(_config['port'], SSHServerFactory(), 
                      interface=_config['bind-address'])

dispatch_loop = network.dispatch_loop
