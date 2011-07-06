'''
AMP server-side client.
@author: Nikita Ofitserov
'''

import functools

from twisted.protocols import amp
from twisted.internet import protocol
from twisted.internet.defer import returnValue, inlineCallbacks

from consys.common import app, network as common_network
from consys.common.ampi import admin
from consys.common.network import AMP_CHANNEL_NAME
from consys.server import hw, network

class AmpServerProtocol(amp.AMP):

    def makeConnection(self, transport):
        amp.AMP.makeConnection(self, transport)
        hw.new_terminal.connect(self.notify_new_terminal)
        hw.terminal_removed.connect(self.notify_terminal_removed)
        hw.terminal_status_updated.connect(self.notify_terminal_status_updated)

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
        return {b'name': terminal.name.encode('utf-8'),
                b'online': terminal.is_online()}

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

    def notify_new_terminal(self, id):
        self.callRemote(admin.NewTerminal, id=id)

    def notify_terminal_removed(self, id):
        self.callRemote(admin.RemovedTerminal, id=id)

    def notify_terminal_status_updated(self, id, online):
        self.callRemote(admin.TerminalStatusUpdated, id=id, online=online)


factory = protocol.Factory() 
factory.protocol = AmpServerProtocol


def on_startup():
    network.admin_connected.connect(on_admin_connected)

def on_admin_connected(avatar):
    ampFactory = functools.partial(common_network.AmpChannel, factory=factory)
    avatar.register_channel(AMP_CHANNEL_NAME, ampFactory)


app.startup.connect(on_startup)
