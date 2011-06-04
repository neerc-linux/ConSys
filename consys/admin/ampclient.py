'''
AMP admin-side client.
@author: Nikita Ofitserov
'''

from notify.all import Signal

from twisted.internet import protocol
from twisted.protocols import amp

from consys.common.ampi import admin
from consys.common import network, log
from consys.admin import login

_log = log.getLogger(__name__)

class AmpClientProtocol(amp.AMP):
    
    @admin.Ping.responder
    def on_ping(self):
        return {}
    
_factory = protocol.Factory() 
_factory.protocol = AmpClientProtocol
    
def on_login():
    channel = network.AmpChannel(factory=_factory)
    login.connection.openChannel(channel)
    def _cbChannel(ch):
        global protocol
        protocol = ch.protocol
        ready(protocol)
    def _ebChannel(failure):
        _log.error('AMP connection is not available')

ready = Signal()
'''Is called when an AMP connection is established.
@param protocol: The AMP protocol instance
@type protocol: AmpClientProtocol
'''

protocol = None

login.successful.connect(on_login)
