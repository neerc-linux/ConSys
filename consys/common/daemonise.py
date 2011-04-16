'''
Daemonisation routines.

@author: Kirill Elagin
'''


import logging
import daemon

import consys.common.config as conf


log = logging.getLogger(__name__)
config = conf.registerSection(None, {
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