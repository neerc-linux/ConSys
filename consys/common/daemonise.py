''' Daemonisation routines.

@author: Kirill Elagin
'''


from __future__ import unicode_literals

import os

from consys.common import log
from consys.common import configuration


_preserved_handles = []

_log = log.getLogger(__name__)
_config = configuration.get_config()


class SimpleContext(object):
    ''' Simple non-daemon context.'''
    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        pass

class PidFile(object):
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        import lockfile
        _log.debug('Writing pid-file {0}'.format(self.path))
        open(self.path, 'w').write('{0}\n'.format(os.getpid()))
        self._lock = lockfile.FileLock(self.path).__enter__()
        return self

    def __exit__(self, *exc):
        self._lock.__exit__(*exc)
        _log.debug('Removing pid-file {0}'.format(self.path))
        os.remove(self.path)


def preserve_handle(*handles):
    _preserved_handles.extend(handles)

def getContext(*args, **kwargs):
    if (_config['daemonise']):
        import daemon
        _log.debug('Running in daemon context')
        if 'pidfile' in kwargs and kwargs['pidfile'] is not None:
            kwargs['pidfile'] = PidFile(kwargs['pidfile'])
        context = daemon.DaemonContext(*args, **kwargs)
        if context.files_preserve is None:
            context.files_preserve = []
        context.files_preserve += _preserved_handles
        return context
    else:
        _log.debug('Running in NON-daemon context')
        return SimpleContext()
