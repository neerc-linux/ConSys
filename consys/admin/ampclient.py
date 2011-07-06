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
    
    @admin.NewTerminal.responder
    def on_new_terminal(self, id):
        new_terminal(id)
        return {}

    @admin.RemovedTerminal.responder
    def on_removed_terminal(self, id):
        terminal_removed(id)
        return {}

    @admin.TerminalStatusUpdated.responder
    def on_terminal_status_updated(self, id, online):
        terminal_status_updated(id, online)
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
    channel.deferred.addCallbacks(_cbChannel, _ebChannel)

ready = Signal()
'''Is called when an AMP connection is established.
@param protocol: The AMP protocol instance
@type protocol: AmpClientProtocol
'''
new_terminal = Signal()
'''Is called when a new terminal is added.
@param id: New terminal id
@type id: int
'''
terminal_removed = Signal()
'''Is called when a terminal is removed.
@param id: Removed terminal id
@type id: int
'''
terminal_status_updated = Signal()
'''Is called when a terminal has come online/offline.
@param id: Updated terminal id
@type id: int
@param online: True if the terminal is online now
@type online: bool
'''

protocol = None

login.successful.connect(on_login)
