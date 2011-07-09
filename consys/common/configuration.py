''' Configuration subsystem.

@author: Kirill Elagin
'''

from __future__ import unicode_literals
from __future__ import print_function

from consys.common import log
from sys import exit
import os
import os.path

import argparse
from configobj import ConfigObj, flatten_errors
from validate import Validator, VdtTypeError

_log = log.getLogger(__name__)


_parser = argparse.ArgumentParser()
_parser.add_argument('-f', dest='daemonise', default=True, action='store_false',
                     help='do not daemonise')
_parser.add_argument('-c', '--config', default='/etc/consys/consys.conf',
                     help='configuration file path (must be absolute in daemon mode) (default: %(default)s)')
_args = _parser.parse_args()

_filepath = _args.config

if _args.daemonise:
    if not os.path.isabs(_filepath):
        _log.critical('In daemon mode config path must be absolute. Exiting.')
        exit(1)
    os.chdir('/')

_workingdir = os.getcwd()
_configpath = os.path.join(_workingdir, _filepath)

_configspec = ConfigObj(_inspec=True, infile={})
_config = ConfigObj(infile=_configpath, file_error=True,
                    configspec=_configspec)
_validator = Validator()
_reload_handlers = []

_config['daemonise'] = _args.daemonise


def _validate_path(value):
    '''
    Check that supplied value is a path, normalise it
    and make absolute (relative to working dir)
    '''
    if value is None:
        return None
    if not isinstance(value, basestring):
        raise VdtTypeError(value)
    return os.path.normpath(os.path.join(_workingdir, value))
_validator.functions['path'] = _validate_path


def filename():
    return _configpath

def get_config(section=None):
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
        _log.critical(section_string + ': ' + unicode(error))
    if res is not True:
        _log.critical('Errors in configuration. Exiting')
        exit()  # FIXME
    if name is None:
        return _config
    else:
        return _config[name]

def register_reload_handler(callback):
    _reload_handlers.append(callback)

def reload(signum=None, frame=None):
    _log.info('Reloading configuration')
    _config.reload()
    for handler in _reload_handlers:
        handler.__call__()
