''' RPC root object for the client
@author: Nikita Ofitserov
'''

import logging

from twisted.spread import pb
from twisted.internet import reactor

from consys.client import dbus, locker, persistent

_log = logging.getLogger(__name__)

TERMINAL_ID_ENTRY = b'terminal-id'

class Root(pb.Referenceable):
    
    def __init__(self):
        self.locker = locker.Locker()
        if not TERMINAL_ID_ENTRY in persistent.storage:
            self.terminal_id = None
            persistent.storage[TERMINAL_ID_ENTRY] = self.terminal_id
        else:
            self.terminal_id = persistent.storage[TERMINAL_ID_ENTRY]
            _log.debug('Terminal id is {0}'.format(self.terminal_id))
    
    def remote_shutdown(self):
        reactor.stop()
        
    def remote_get_locker(self):
        return self.locker
    
    def remote_get_terminal_id(self):
        return self.terminal_id
    
    def remote_set_terminal_id(self, id):
        _log.info('Got assigned terminal id {0}'.format(id))
        self.terminal_id = id
        persistent.storage[TERMINAL_ID_ENTRY] = id

    def remote_call_dbus(self, bus, bus_name, object_path, iface_name,
                            method, args):
        def callback(retval):
            _log.debug('DBus call {0} returned result: {1}'.format(method,
                                                                   retval))
        def errback(failure):
            _log.debug('DBus call {0} returned failure: {1}'.format(method,
                                                                    failure))
        if bus == 'system':
            bus = dbus.system_bus()
        elif bus == 'session':
            bus = dbus.session_bus()
        else:
            _log.warning('Unknown DBus bys type: {0}'.format(bus))
            return
        d = bus.get_object(bus_name, object_path).call(method, iface_name,
                                                       *args)
        return d.addCallbacks(callback, errback)
