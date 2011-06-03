''' Common network routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals 

from consys.common import log

from twisted.internet import reactor, base, defer
from twisted.conch.ssh import channel

_log = log.getLogger(__name__)


RPC_CHANNEL_NAME = b'rpc@consys'

class RpcChannel(channel.SSHChannel):
    name = RPC_CHANNEL_NAME

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
        self.protocol = self.factory.buildProtocol(None)
        self.protocol.makeConnection(self)

    def dataReceived(self, data):
        self.protocol.dataReceived(data)

