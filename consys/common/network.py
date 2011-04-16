''' Common network routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals 

import base64
import logging
import asyncore
import paramiko

from consys.common import scheduler

_log = logging.getLogger(__name__)

__all__ = [
           'CHANNEL_NAME',
           'CONTROL_SYBSYSTEM',
           'RPC_C2S_SYBSYSTEM',
           'RPC_S2C_SYBSYSTEM',
           'OPEN_S2C_MESSAGE',
           'NetworkError',
           'AsyncMixIn',
           'SubsystemHandler',
           'load_public_key'
          ]


CHANNEL_NAME = b'session@consys'
CONTROL_SYBSYSTEM = b'control@consys'
RPC_C2S_SYBSYSTEM = b'rpc-c2s@consys'
RPC_S2C_SYBSYSTEM = b'rpc-s2c-{0}@consys'
OPEN_S2C_MESSAGE = b's2c-open-channel'

class NetworkError(Exception):
    ''' Base class for all network-related errors. '''
    pass

class AsyncMixIn(object):
    ''' A mix-in for asyncore dispatchers. '''
    pass

class SubsystemHandler(asyncore.dispatcher_with_send):
    def __init__(self, channel, name, server):
        asyncore.dispatcher_with_send.__init__(self, channel)
        self.__channel = channel
        self.__transport = channel.get_transport()
        self.__name = name
        self.__server = server
        
    def handle_start(self):
        pass
        
    def start(self):
        pass

def load_public_key(filename):
    with open(filename) as f:
        line = f.readline()
    fields = line.split(' ')
    if len(fields) != 3 or fields[0] != b'ssh-rsa':
        raise NetworkError('Cannot read public key '
                           'file \'{0}\''.format(filename))
    return paramiko.RSAKey(data=base64.decodestring(fields[1])) 
