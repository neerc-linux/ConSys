''' Common network routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals 

import base64
import logging
import paramiko

log = logging.getLogger(__name__)

CHANNEL_NAME = b'session@consys'
CONTROL_SYBSYSTEM = b'control@consys'
RPC_C2S_SYBSYSTEM = b'rpc-c2s@consys'
RPC_S2C_SYBSYSTEM = b'rpc-s2c-{}@consys'

class NetworkError(Exception):
    ''' Base class for all network-related errors. '''
    pass

def load_public_key(filename):
    with open(filename) as f:
        line = f.readline()
    fields = line.split(' ')
    if len(fields) != 3 or fields[0] != b'ssh-rsa':
        raise NetworkError('Cannot read public key '
                           'file \'{0}\''.format(filename))
    return paramiko.RSAKey(data=base64.decodestring(fields[1])) 
