''' Server-side network routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals

import base64
import hashlib

from zope.interface import implements
from notify.all import Signal
from twisted.conch import avatar
from twisted.conch.checkers import SSHPublicKeyDatabase
from twisted.conch.insults import insults
from twisted.conch.manhole import ColoredManhole
from twisted.conch.manhole_ssh import TerminalSession
from twisted.conch.ssh import session, keys, factory, userauth, connection
from twisted.cred import portal
from twisted.cred.checkers import FilePasswordDB
from twisted.internet import reactor
from twisted.python import components
from twisted.spread import pb

from consys.common import log
from consys.common import configuration, network, app

__all__ = ['on_startup', 'client_connected', 'client_disconnected']

_config = configuration.register_section('network',
     {
        'bind-address': 'string(default=0.0.0.0)',
        'port': 'integer(min=1, max=65535, default=2222)',
        'server-key': 'path(default=keys/server)',
        'client-public-key': 'path(default=keys/client.pub)',
        'client-user-name': 'string(default=terminal)',
        'user-auth-db': 'path(default=data/admins.txt)'
     })

_log = log.getLogger(__name__)

class ClientAvatar(avatar.ConchUser, pb.Root):

    def __init__(self):
        avatar.ConchUser.__init__(self)
        self.terminalId = None
        self.rpcFactory = pb.PBServerFactory(self)

    def __repr__(self):
        return '<ClientAvatar(terminalID: {0})>'.format(self.terminalId)

    def loggedIn(self):
        channel = network.RpcChannel(factory=self.rpcFactory)
        self.conn.openChannel(channel)
    
    def remote_set_mind(self, mind):
        self.mind = mind
        client_connected(self)
        _log.info('RPC connection ready')    
    
    def loggedOut(self):
        client_disconnected(self)
        

class AdminAvatar(avatar.ConchUser, pb.Root):

    def __init__(self, username):
        avatar.ConchUser.__init__(self)
        self.username = username
        self.namespace = {
                          'self': self,
                          'reactor': reactor,
                          }
        self.channelLookup.update({'session': session.SSHSession})

    def loggedIn(self):
        pass
    
    def loggedOut(self):
        pass


class AdminTerminalSession(TerminalSession):
    chainedProtocolFactory = lambda self: \
        insults.ServerProtocol(ColoredManhole, self.original.namespace)
    

components.registerAdapter(AdminTerminalSession, AdminAvatar, session.ISession)


class ExampleRealm:
    implements(portal.IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        if avatarId == _config['client-user-name']:
            avatar = ClientAvatar()
        else:
            avatar = AdminAvatar(avatarId)
        # (implemeted_iface, avatar, logout_callable)
        return interfaces[0], avatar, avatar.loggedOut


class InMemoryPublicKeyChecker(SSHPublicKeyDatabase):

    def __init__(self, username, publickey):
        self.username = username
        self.publickey = publickey

    def checkKey(self, credentials):
        return credentials.username == self.username and \
            self.publickey.blob() == credentials.blob


class SSHConnection(connection.SSHConnection):
    '''A server side of the SSH connection.'''
    
    def serviceStarted(self):
        connection.SSHConnection.serviceStarted(self)
        _log.info('SSH connection ready')
        self.transport.avatar.loggedIn()
        
    def serviceStopped(self):
        connection.SSHConnection.serviceStopped(self)
        

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
    else:
        return 'bad-hash-algorithm'

_portal = portal.Portal(ExampleRealm())
_portal.registerChecker(FilePasswordDB(_config['user-auth-db'],
                                      hash=_htpasswd_hash, cache=True))
_portal.registerChecker(
    InMemoryPublicKeyChecker(_config['client-user-name'],
                             keys.Key.fromFile(_config['client-public-key'])))
SSHServerFactory.portal = _portal

def on_startup():
    reactor.listenTCP(_config['port'], SSHServerFactory(), 
                      interface=_config['bind-address'])

app.startup.connect(on_startup)

client_connected = Signal()
''' Is emitted when a client connects.
@param avatar: Client's avatar
@type avatar: ClientAvatar 
'''
client_disconnected = Signal()
''' Is emitted when a client disconnects.
@param avatar: Client's avatar
@type avatar: ClientAvatar 
'''
