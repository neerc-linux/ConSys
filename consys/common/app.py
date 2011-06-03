'''
Global startup and shutdown events
@author: Nikita Ofitserov
'''

from notify.all import Signal

from twisted.internet import reactor

startup = Signal()
''' Is emitted when the app starts.
'''

shutdown = Signal()
''' Is emitted when the app shuts down.
'''

def dispatch_loop():
    '''Dispatches messages until program shutdown.'''
    reactor.addSystemEventTrigger('before', 'shutdown', shutdown)
    reactor.run()
