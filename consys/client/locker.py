'''
Manage desktop locking
@author: Nikita Ofitserov
'''

import logging

from twisted.internet.defer import inlineCallbacks
from twisted.spread import pb

from consys.common import configuration
from consys.client import dbus

_log = logging.getLogger(__name__)

_config = configuration.register_section('locker', 
    {
        'use-plasma': 'boolean(default=true)',
    })

class Locker(pb.Referenceable):
    screensaver_path = (b'org.freedesktop.ScreenSaver', b'/ScreenSaver')
    plasma_overlay_path = (b'org.kde.plasma-overlay', b'/App')
    
    def __init__(self):
        object = dbus.session_bus().get_object(*self.screensaver_path)
        self.screensaver = object.get_interface(b'org.freedesktop.ScreenSaver')
        
    def lock(self):
        d = self.screensaver.call(b'Lock')
        def callback(retval):
            _log.debug('Screen locked')
        def errback(failure):
            _log.error('Failed to lock screen: {0}'.format(failure))
        return d.addCallbacks(callback, errback)
    
    def unlock(self):
        d = self.screensaver.call(b'SetActive', False)
        def callback(retval):
            if _config['use-plasma']:
                plasma = \
                    dbus.session_bus().get_object(*self.plasma_overlay_path)
                d = plasma.call(b'quit', b'org.kde.plasmaoverlay.App')
                return d.addCallbacks(callbackFinal, errback)                
            else:
                return callbackFinal(retval)
        def callbackFinal(retval):
            _log.debug('Screen unlocked')
        def errback(failure):
            _log.error('Failed to unlock screen: {0}'.format(failure))
        return d.addCallbacks(callback, errback)
    
    def remote_lock(self):
        return self.lock()

    def remote_unlock(self):
        return self.unlock()
