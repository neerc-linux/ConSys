'''
AMP server-side client.
@author: Nikita Ofitserov
'''
from twisted.protocols import amp
from twisted.internet import protocol
from twisted.internet.defer import returnValue, inlineCallbacks

from consys.common.ampi import admin
from consys.server import hw

class AmpServerProtocol(amp.AMP):
    
    @admin.Ping.responder
    def on_ping(self):
        return {}

    @admin.GetTerminals.responder
    def get_terminals(self):
        return {b'ids': hw.manager.terminals.keys()}
    
    @admin.GetTerminalData.responder
    def get_terminal_data(self, id):
        try:
            terminal = hw.manager.terminals[id]
        except KeyError:
            raise admin.NoSuchObjectError('Terminal {0} not found'.format(id))
        return {b'name': terminal.name, b'online': terminal.is_online()}
    
    @admin.ShutdownTerminal.responder
    def shutdown_terminal(self, id):
        try:
            terminal = hw.manager.terminals[id]
        except KeyError:
            raise admin.NoSuchObjectError('Terminal {0} not found'.format(id))
        if not terminal.is_online():
            raise admin.TerminalOfflineError('Terminal {0}'
                                             ' is offline'.format(id))
        @inlineCallbacks
        def _do_shutdown():
            yield terminal.client.callRemote(b'shutdown')
            returnValue({})
        return _do_shutdown()
    

factory = protocol.Factory() 
factory.protocol = AmpServerProtocol
  
