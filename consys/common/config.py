'''
Configuration subsystem.
@author: Kirill Elagin
'''

from __future__ import unicode_literals
from __future__ import print_function

import logging
from sys import exit

from configobj import ConfigObj, flatten_errors
from validate import Validator

log = logging.getLogger(__name__)

_filename = '/etc/consys/config.ini'
_configspec = ConfigObj(_inspec=True, infile={})
_config = ConfigObj(infile=_filename, configspec=_configspec)
_validator = Validator()
_reload_handlers = []

def get_config(section):
    if _config is not None:
        if section is None:
            return _config
        else:
            return _config[section]
    else:
        return None

def register_section(name, dict):
    if name is None:
        _configspec.update(dict)
    else:
        _configspec[name] = dict
    res = _config.validate(_validator, preserve_errors=True)
    for section_list, key, error in flatten_errors(_config, res):
        if key is not None:
            section_list.append(key)
        else:
            section_list.append('[missing section]')
        section_string = ' -> '.join(section_list)
        if error == False:
            error = 'Missing value or section'
        log.critical(section_string + ': ' + unicode(error))
    if res is not True:
        log.critical('Errors in configuration. Exiting')
        exit()  # FIXME
    if name is None:
        return _config
    else:
        return _config[name]

def register_reload_handler(callback):
    _reload_handlers.append(callback)

def reload(signum, frame):
    log.info('Reloading configuration')
    _config.reload()
    for handler in _reload_handlers:
        handler.__call__()