'''
Contest hardware management
@author: Nikita Ofitserov
'''

from __future__ import unicode_literals


from notify.signal import Signal

from twisted.internet.defer import inlineCallbacks, returnValue

from consys.common import log
from consys.server import persistent, network

_log = log.getLogger(__name__)

class StateError(Exception):
    '''
    Indicates that a transition while in an illegal hardware state was requested.
    '''

class Terminal(persistent.Base):
    '''
    Represents a contest terminal (computer capable of being a workstation).
    
    Table structure:
      id :: INTEGER, primary_key
      name :: TEXT
      workstation_id :: INTEGER, can be NULL
    '''
    TABLENAME = 'terminals'
    BELONGS_TO = ['workstation']

    def __init__(self, **kwargs):
        persistent.Base.__init__(self, **kwargs)
        self.client = None
    
    def __repr__(self):
        return '<Terminal(id: {0}, {1}'\
               ')>'.format(self.id, 'online' if self.client else 'offline')
    
    def connect(self, client):
        if self.is_online():
            raise StateError('Client {0} cannot connect to {1}'.format(client,
                                                                       self))
        self.client = client
        client.terminalId = self.id
    
    def disconnect(self):
        if not self.is_online():
            raise StateError('Terminal {0} cannot be disconnected'.format(self))
        self.client.terminalId = None
        self.client = None
    
    def is_online(self):
        return self.client is not None


class Workstation(persistent.Base):
    '''
    Represents a workstation (logical team working place).

    Table structure:
      id :: INTEGER, primary_key
      name :: TEXT
    '''
    TABLENAME = 'workstations'
    HASONE = ['terminal']

    def __init__(self, **kwargs):
        persistent.Base.__init__(self, **kwargs)

    def __repr__(self):
        return '<Workstation(id: {0}, terminal: {1}'\
               ')>'.format(self.id, self.terminal)


class Manager(object):
    '''
    Manages all hardware, keeping track of network events.
    '''
    def __init__(self):
        persistent.ready.connect(self.on_db_ready)
        network.client_connected.connect(self.on_client_connection)
        network.client_disconnected.connect(self.on_client_disconnect)

    @inlineCallbacks
    def create_terminal(self):
        freeid = max(self.terminals.keys() + [0]) + 1
        terminal = Terminal(name='PC#{0}'.format(freeid))
        terminal = yield terminal.save()
        self.terminals[terminal.id] = terminal
        _log.debug('Created terminal {0}'.format(terminal.id))
        new_terminal(terminal.id)
        returnValue(terminal)

    @inlineCallbacks
    def create_workstation(self, name):
        workstation = Workstation(name=name)
        workstation = yield workstation.save()
        self.workstations[workstation.id] = workstation
        _log.debug('Created workstation {0}'.format(workstation.id))
        new_workstation(workstation.id)
        returnValue(workstation)

    @inlineCallbacks
    def on_client_connection(self, avatar):
        terminal_id = yield avatar.mind.callRemote(b'get_terminal_id')
        if terminal_id is None or terminal_id not in self.terminals:
            terminal = yield self.create_terminal()
            yield avatar.mind.callRemote(b'set_terminal_id', terminal.id)
        else:
            terminal = self.terminals[terminal_id]
        terminal.connect(avatar)
        terminal_status_updated(terminal_id, True)
        _log.debug('Updated terminal status: {0}'.format(repr(terminal)))
    
    def on_client_disconnect(self, avatar):
        for terminal in self.terminals.values():
            if terminal.client == avatar:
                terminal.disconnect()
                _log.debug('Updated terminal status:'
                           ' {0}'.format(repr(terminal)))
                terminal_status_updated(terminal.id, False)
    
    @inlineCallbacks
    def on_db_ready(self):
        def dictify(ls):
            return dict(map(lambda e: (e.id, e), ls))
        ts = yield Terminal.all()
        self.terminals = dictify(ts)
        _log.info('Loaded {0} terminals from DB'.format(len(self.terminals)))
        _log.debug('Terminals: {0}'.format(self.terminals))
        ws = yield Workstation.all()
        self.workstations = dictify(ws)
        _log.info('Loaded {0} workstations from '
                  'DB'.format(len(self.workstations)))
        _log.debug('Workstations: {0}'.format(self.workstations))


persistent.register_classes(Terminal, Workstation)

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
new_workstation = Signal()
'''Is called when a new workstation is added.
@param id: New workstation id
@type id: int
'''
workstation_removed = Signal()
'''Is called when a workstation is removed.
@param id: Removed workstation id
@type id: int
'''

manager = Manager()
