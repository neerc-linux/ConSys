'''
Daemonisation routines.

@author: Kirill Elagin
'''


from __future__ import unicode_literals

import daemon

from consys.common import log
from consys.common import configuration


_preserved_handles = []

_log = log.getLogger(__name__)

_config = configuration.register_section(None,
    {
        'daemonise': 'boolean(default=True)',
    })


class SimpleContext(object):
    ''' Simple non-daemon context.'''
    def __enter__(self):
        pass
    def __exit__(self, type, value, tb):
        pass


def preserve_handle(*handles):
    _preserved_handles.extend(handles)

def getContext(*args, **kwargs):
    if (_config['daemonise']):
        _log.debug('Running in daemon context')
        context = daemon.DaemonContext(*args, **kwargs)
        if context.files_preserve is None:
            context.files_preserve = []
        context.files_preserve += _preserved_handles
        return context
    else:
        _log.debug('Running in NON-daemon context')
        return SimpleContext()
