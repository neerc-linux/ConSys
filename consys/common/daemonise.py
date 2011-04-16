''' Daemonisation routines.

@author: Kirill Elagin
'''


import logging
import daemon

from consys.common import configuration


log = logging.getLogger(__name__)

config = configuration.register_section(None, 
    {
        'daemonise': 'boolean(default=True)',
    })


class SimpleContext(object):
    ''' Simple non-daemon context.'''
    def __enter__(self):
        pass
    def __exit__(self, type, value, tb):
        pass


def getContext(*args, **kwargs):
    if (config['daemonise']):
        log.debug('Running in daemon context')
        return daemon.DaemonContext(*args, **kwargs)
    else:
        log.debug('Running in NON-daemon context')
        return SimpleContext()
