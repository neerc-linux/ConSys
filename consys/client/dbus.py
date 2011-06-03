'''
DBus integration module, using twisted Deferreds
@author: Nikita Ofitserov
'''

from __future__ import absolute_import

import dbus

from consys.common import log

from twisted.internet import defer

_log = log.getLogger(__name__)

class Bus:
    def __init__(self, bus):
        self.bus = bus
        
    def get_object(self, bus_name, object_path):
        return Object(self.bus.get_object(bus_name, object_path))
    
    def close(self):
        self.bus.close()
        

class Object:
    def __init__(self, object):
        self.object = object
        
    def get_interface(self, iface_name):
        return Interface(dbus.Interface(self.object, iface_name))
    
    def call(self, method_name, iface_name, *args):
        method = self.object.get_dbus_method(method_name, iface_name)
        return _do_call(method, args)


class Interface:
    def __init__(self, iface):
        self.iface = iface
        
    def call(self, method_name, *args):
        method = self.iface.get_dbus_method(method_name)
        return _do_call(method, args)
    

class AsyncHandler:
    def __init__(self):
        self.deferred = defer.Deferred()
    
    def get_deferred(self):
        return self.deferred
    
    def callback(self, *results):
        if len(results) == 0:
            result = None
        elif len(results) == 1:
            result = results[0]
        else:
            result = tuple(results)
        self.deferred.callback(result)
        
    def errback(self, exception):
        self.deferred.errback(exception)


def _do_call(method, args):
    handler = AsyncHandler()
    method(reply_handler=handler.callback, error_handler=handler.errback,
           *args)
    return handler.get_deferred()

_system_bus = None
_session_bus = None

def system_bus():
    global _system_bus
    if _system_bus is None:
        _system_bus = Bus(dbus.SystemBus()) 
    return _system_bus

def session_bus():
    global _session_bus
    if _session_bus is None:
        _session_bus = Bus(dbus.SessionBus()) 
    return _session_bus


# Make dbus-python use GLib reactor
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)
