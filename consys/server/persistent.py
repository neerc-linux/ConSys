'''
Persistent storage support. Based on Twistar/SQLite3.
@author: Nikita Ofitserov
'''

from __future__ import unicode_literals

from urlparse import urlparse

from notify.all import Signal
from twistar.registry import Registry
from twistar.dbobject import DBObject
from twistar.dbconfig.base import InteractionBase

from twisted.enterprise import adbapi

from consys.common import log
from consys.common import configuration, app

_config = configuration.register_section('server-persistence', 
    {
        'db-url': 'string(default=sqlite:///data/server.db)',
    })

_log = log.getLogger(__name__)

def _handle_sqlite(parsed_url):
    return ('sqlite3', {
            'database': parsed_url.path[1:],
            'check_same_thread': False,
            })

_drivers = {'sqlite': _handle_sqlite}

Base = DBObject

ready = Signal()
'''Is emitted when the database becomes available'''

def on_startup():
    parsed_url = urlparse(_config['db-url'])
    driver, args = _drivers[parsed_url.scheme](parsed_url)
    Registry.DBPOOL = adbapi.ConnectionPool(driver, **args)
    InteractionBase.LOG = True
    ready()

app.startup.connect(on_startup)
