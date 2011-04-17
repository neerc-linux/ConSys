''' Client-side network routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals 

import logging
import time
import asynchat
import json
import threading
import numbers
import paramiko

from consys.common import configuration
from consys.common.network import dispatch_loop, load_public_key, \
    CHANNEL_NAME, CONTROL_SYBSYSTEM, RPC_C2S_SYBSYSTEM, RPC_S2C_SYBSYSTEM,\
    AsyncMixIn, OPEN_S2C_MESSAGE, IncomingRequestHandler, OutgoingRequestHandler
from consys.common.scheduler import Future

config = configuration.register_section('network', 
    {
        'server-address': 'string()',
        'port': 'integer(min=1, max=65535, default=2222)',
        'client-key': 'string(default=/etc/consys/keys/client)',
        'server-public-key': 'string(default=/etc/consys/keys/server.pub)',
        'client-user-name': 'string(default=test)',
    })

_log = logging.getLogger(__name__)

class ControlChannelListener(threading.Thread):
    '''A thread for listening on the control channel and opening 
    reverse channels.
    '''
    def __init__(self, client, channel):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.client = client
        self.channel = channel
        self.socket = channel.makefile()
        
    def run(self):
        while True:
            line = self.socket.readline()
            _log.debug('Got control message: "{0}"'.format(line))
            time.sleep(5)

class ControlRequestHandler(AsyncMixIn, asynchat.async_chat):

    def __init__(self, client, sock):
        asynchat.async_chat.__init__(self, sock=sock)
        self.client = client
        self.ibuffer = []
        self.obuffer = ''
        self.set_terminator('\0')
        self.handling = False

    def collect_incoming_data(self, data):
        '''Buffer the data'''
        self.ibuffer.append(data)

    def found_terminator(self):
        data = ''.join(self.ibuffer)
        self.ibuffer = []
        try:
            request = json.loads(data)
        except ValueError:
            _log.error('Invalid control request from server:'
                      ' "{0}"'.format(data))
        _log.debug('Control request: "{0}"'.format(request))
        if not isinstance(request, list) or len(request) == 0:
            _log.error('Invalid control request')
            return
        cmd = request[0]
        args = request[1:]
        if cmd == OPEN_S2C_MESSAGE:
            if len(args) != 1 or not isinstance(args[0], numbers.Integral):
                _log.error('Invalid control command')
                return
            id = int(args[0])
            self.client.open_s2c_channel(id)
        else:
            _log.error('Unknown control command')


class SSHClient(object):
    '''A SSH protocol client.'''
    
    def __init__(self):
        '''Initializes the client and connects it to the server.
        '''
        self.transport = paramiko.Transport((config['server-address'],
                                             config['port']))
        self.client_pkey = \
            paramiko.RSAKey.from_private_key_file(config['client-key'])
        self.server_key = load_public_key(config['server-public-key'])
        self.username = config['client-user-name']
        self.transport.connect(self.server_key, self.username,
                               None, self.client_pkey)
        del self.client_pkey
        self.control_channel = self.transport.open_channel(CHANNEL_NAME)
        self.control_channel.invoke_subsystem(CONTROL_SYBSYSTEM)
#        self.control_listener = ControlChannelListener(self,
#                                                       self.control_channel)
#        self.control_listener.start()
        self.control_handler = ControlRequestHandler(self, self.control_channel)
        # XXX: test only
        future = self.send_async(b'What is the answer?')
        future.set_callback(self.complete)
        
    def complete(self, future):
        answer = future.get_result()
        _log.debug("Received answer: {0}".format(answer))
    
    def send_async(self, data):
        '''Creates a new channel, sends out the data and receives an answer.
        All work is done asynchronously. The return value is a future for the
        answer.
        '''
        channel = self.transport.open_channel(CHANNEL_NAME)
        channel.invoke_subsystem(RPC_C2S_SYBSYSTEM)
        future = Future()
        OutgoingRequestHandler(channel, data, future.set_result)
        return future
    
    def handle_request(self, request):
        _log.debug('Handling S2C request "{0}"'.format(request))
        return b'42'

    def open_s2c_channel(self, id):
        _log.debug('Opening S2C channel with id "{0}"'.format(id))
        channel = self.transport.open_channel(CHANNEL_NAME)
        channel.invoke_subsystem(RPC_S2C_SYBSYSTEM.format(id))
        IncomingRequestHandler(channel, self.handle_request)
