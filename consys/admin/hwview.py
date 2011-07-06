'''
Things related to contest hardware representation.
@author: Nikita Ofitserov
'''

import functools

from PyQt4 import QtCore
from twisted.internet.defer import inlineCallbacks, returnValue

from consys.common import log
from consys.common.ampi import admin
from consys.admin import ampclient

_log = log.getLogger(__name__)

class HardwareModel(QtCore.QAbstractTableModel):
    '''
    A model for hardware representation.
    Contains columns:
        name :: string
        online :: boolean
    '''

    COLUMN_COUNT = 2

    def __init__(self):
        QtCore.QAbstractTableModel.__init__(self)
        self.rows = []

    def setData(self, data):
        '''Fills model with specified data.
        @type data: sequence of tuples (id, name, status)
        '''
        self.rows = []
        self.map = {}
        for id, name, status in data:
            self._insertData(id, name, status)
        self.reset()

    def _insertData(self, id, name, status):
        self.map[id] = len(self.rows)
        self.rows.append([unicode(name), bool(status)])

    def insertData(self, id, name, status):
        self._insertData(id, name, status)
        self.reset()

    def removeData(self, id):
        self.rows.pop(self.map[id])
        del self.map[id]
        self.reset()

    def updateStatus(self, id, status):
        _log.debug('Updating status: terminal {0} is '
                   '{1}'.format(id, 'online' if status else 'offline'))
        index = self.map[id]
        self.rows[index][1] = status
        self.reset()

    def rowCount(self, parent):
        return len(self.rows)

    def columnCount(self, parent):
        return self.COLUMN_COUNT

    def data(self, index, role):
        if index.isValid():
            row = index.row()
            #_log.debug((row, index.column(), role))
            if row >= 0 and row < self.rowCount(None):
                name, status = self.rows[row]
                if role == QtCore.Qt.DisplayRole:
                    if index.column() == 0: # name
                        return QtCore.QVariant(name)
                    if index.column() == 1: # status
                        return QtCore.QVariant(status)
        return QtCore.QVariant(QtCore.QVariant.Invalid)


@inlineCallbacks
def get_terminal_data(id):
    ans = yield ampclient.protocol.callRemote(admin.GetTerminalData, id=id)
    returnValue((id, ans['name'].decode('utf-8'), ans['online']))

def connect_model(model):
    ampclient.ready.connect(functools.partial(fetch_hardware, model=model))
    @inlineCallbacks
    def new_terminal(id):
        data = yield get_terminal_data(id)
        model.insertData(*data)
    ampclient.new_terminal.connect(new_terminal)
    ampclient.terminal_removed.connect(model.removeData)
    ampclient.terminal_status_updated.connect(model.updateStatus)

@inlineCallbacks
def fetch_hardware(server, model):
    _log.debug('Fetching hardware...')
    ans = yield server.callRemote(admin.GetTerminals)
    terminalIds = ans['ids']
    terminals = []
    for id in terminalIds:
        data = yield get_terminal_data(id)
        terminals.append(data)
    _log.debug('Terminals: {0}'.format(terminals))
    model.setData(terminals)
