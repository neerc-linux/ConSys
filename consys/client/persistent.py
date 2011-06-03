'''
Persistent storage support. Based on Shelve.
@author: Nikita Ofitserov
'''

from __future__ import unicode_literals

import logging
import shelve

from notify.all import Signal


from consys.common import configuration, app

_config = configuration.register_section('client-persistence', 
    {
        'db-file': 'string(default=data/client.db)',
    })

_log = logging.getLogger(__name__)

ready = Signal()
'''Is emitted when the storage becomes available'''

storage = None
'''The storage dict-like object'''

def on_startup():
    global storage
    storage = shelve.open(_config['db-file'])
    ready()

def on_shutdown():
    storage.close()

app.startup.connect(on_startup)
app.shutdown.connect(on_shutdown)
