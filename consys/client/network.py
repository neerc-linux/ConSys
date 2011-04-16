''' Client-side network routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals 

import logging
import time
import asynchat
import json
import threading
import paramiko

from consys.common import configuration
from consys.common.network import load_public_key, CHANNEL_NAME, \
    CONTROL_SYBSYSTEM, RPC_C2S_SYBSYSTEM, RPC_S2C_SYBSYSTEM

config = configuration.register_section('network', 
    {
        'server-address': 'string()',
        'port': 'integer(min=1, max=65535, default=2222)',
        'client-key': 'string(default=/etc/consys/keys/client)',
        'server-public-key': 'string(default=/etc/consys/keys/server.pub)',
        'client-user-name': 'string(default=test)',
    })

log = logging.getLogger(__name__)

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
            log.debug('Got control message: \'{0}\''.format(line))
            time.sleep(5)

class control_request_handler(asynchat.async_chat):

    def __init__(self, sock):
        asynchat.async_chat.__init__(self, sock=sock)
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
            log.error('Invalid control request from server:'
                      ' \'{0}\''.format(data))
        log.debug('Control request: \'{0}\''.format(request))

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
        self.control_listener = ControlChannelListener(self,
                                                       self.control_channel)
        self.control_listener.start()
        time.sleep(10)
        
    def interact(self, subsytem, data):
        '''Creates a new channel using specified subsystem, sends out the data 
        and receives an answer. The answer is returned.
        '''
        channel = self.transport.open_channel(CHANNEL_NAME)
        channel.invoke_subsystem(RPC_C2S_SYBSYSTEM)
        channel.sendall(str(data))
        f = channel.makefile()
        answer = f.read()
        return answer

