'''
AMP admin-side client.
@author: Nikita Ofitserov
'''

from twisted.protocols import amp

from consys.common.ampi import admin
from consys.common import network
from consys.admin import login
from twisted.internet import protocol

class AmpClientProtocol(amp.AMP):
    
    @admin.Ping.responder
    def on_ping(self):
        return {}
    
_factory = protocol.Factory() 
_factory.protocol = AmpClientProtocol
    
def on_login():
    login.connection.openChannel(network.AmpChannel(factory=_factory))

login.successful.connect(on_login)