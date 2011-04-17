''' Common network routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals 

import base64
import logging
import asyncore
import asynchat
import paramiko

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
           'load_public_key',
           'dispatch_loop'
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


class IncomingRequestHandler(AsyncMixIn, asynchat.async_chat):
    ''' Handles incoming data sends '''
    
    def __init__(self, socket, callback):
        asynchat.async_chat.__init__(self, socket)
        self.set_terminator(None)
        self.callback = callback
        self.inbuffer = []
        self.writing = False
        
    def collect_incoming_data(self, data):
        if data != '':
            _log.debug('IN read')
            self.inbuffer.append(data)
        else:
            # EOF received
            self.socket.shutdown_read()
            request = ''.join(self.inbuffer)
            self.inbuffer = []
            _log.debug('IN request: "{0}"'.format(request))
            answer = self.callback(request)
            _log.debug('IN answer: "{0}"'.format(answer))
            self.push(answer)
            self.close_when_done()


class OutgoingRequestHandler(AsyncMixIn, asynchat.async_chat):
    ''' Handles outgoing data sends '''
    
    def __init__(self, socket, data, callback):
        asynchat.async_chat.__init__(self, socket)
        self.set_terminator(None)
        self.callback = callback
        self.inbuffer = []
        _log.debug('OUT request: "{0}"'.format(data))
        self.writing = True
        producer = asynchat.simple_producer(data, 2048)
        self.producer_fifo.append(producer)
        self.producer_fifo.append(None)
        self.initiate_send()
        
    def collect_incoming_data(self, data):
        if data != '':
            _log.debug('OUT read')
            self.inbuffer.append(data)
        else:
            # EOF received
            answer = ''.join(self.inbuffer)
            _log.debug('OUT answer: "{0}"'.format(answer))
            self.callback(answer)
            self.close()

    def handle_close(self):
        _log.debug('OUT close')
        if self.writing:
            self.socket.shutdown_write()
            self.writing = False


def load_public_key(filename):
    with open(filename) as f:
        line = f.readline()
    fields = line.split(' ')
    if len(fields) != 3 or fields[0] != b'ssh-rsa':
        raise NetworkError('Cannot read public key '
                           'file \'{0}\''.format(filename))
    return paramiko.RSAKey(data=base64.decodestring(fields[1])) 

def dispatch_loop():
    '''Dispatches messages until all dispatchers are closed.'''
    asyncore.loop()
