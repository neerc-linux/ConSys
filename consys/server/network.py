''' Server-side network routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals 

import logging
import socket
import asyncore
import json
import threading
import paramiko

from consys.common import configuration
from consys.common.network import *


__all__ = ['SSHServer']

_config = configuration.register_section('network',
     {
        'bind-address': 'string(default=0.0.0.0)',
        'port': 'integer(min=1, max=65535, default=2222)',
        'server-key': 'string(default=/etc/consys/keys/server)',
        'client-public-key': 'string(default=/etc/consys/keys/client.pub)',
        'client-user-name': 'string(default=test)',
     })

_log = logging.getLogger(__name__)

class ControlSubsystemHandler(SubsystemHandler):
    '''Server-to-client control subsystem handler.'''
    
    def __init__(self, channel, name, server, connection):
        SubsystemHandler.__init__(self, channel, name, server)
        self.connection = connection
        _log.debug('Incoming control channel!')
        connection.set_control_handler(self)

class RPCSubsystemHandler(paramiko.SubsystemHandler):
    '''Client-to-server RPC subsystem handler.'''
    
    def start_subsystem(self, name, transport, channel):
        '''Request handling logic.'''
        _log.debug('Incoming C2S RPC channel!')
        
class RPCReverseSubsystemHandler(paramiko.SubsystemHandler):
    '''Server-to-client RPC subsystem handler.'''
    
    def start_subsystem(self, name, transport, channel):
        '''Request handling logic.'''
        _log.debug('Incoming S2C RPC back-channel!')

class SSHConnection(object):
    '''A server side of the SSH connection.'''
    
    def __init__(self, socket, server):
        '''Creates a SSH server-side endpoint.'''
        self.server = server
        self.server.connections.append(self)
        self.transport = paramiko.Transport(socket)
        self.transport.add_server_key(server.server_pkey)
        self.transport.start_server(server=ServerImpl(self))
        self.control_event = threading.Event()
        self.transport.set_subsystem_handler(CONTROL_SYBSYSTEM, 
                                             ControlSubsystemHandler, self)
        self.transport.set_subsystem_handler(RPC_C2S_SYBSYSTEM, 
                                             RPCSubsystemHandler)
        self.control_handler = None
        self.next_s2c_id = 0
        self.s2c_lock = threading.Lock()
        if not self.control_event.wait(1): # wait 1 second for the client
            raise NetworkError('Client has not connected control channel '
                               'in time')
        
    def set_control_handler(self, handler):
        '''Sets the control channel handler, if not already set.'''
        if self.control_handler is None:
            self.control_event.set()
            self.control_handler = handler
            
    def send_channel_request(self):
        '''Requests a new S2C channel to be opened'''
        if self.control_handler is None:
            raise NetworkError('Client control channel is not connected')
        with self.s2c_lock:
            request = [OPEN_S2C_MESSAGE, self.next_s2c_id]
            self.next_s2c_id += 1
        data = json.dumps(request) + '\0'
        self.control_handler.send(data)

    def close(self):
        '''Closes the connection.'''
        # FIXME: clean up gracefully
        _log.info('Closing SSH connection')
        self.transport.close()
        self.server.connections.remove(self)
        
        
class ServerImpl(paramiko.ServerInterface):
    '''A concrete ServerInterface implementation.'''
    
    def __init__(self, connection):
        self.connection = connection
        
    def handle_disconnect(self):
        self.connection.close()
        
    def get_allowed_auths(self, username):
        return b'publickey'
    
    def check_auth_publickey(self, username, key):
        server = self.connection.server
        if username == server.username and key == server.client_key:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED
    
    def check_channel_request(self, kind, chanid):
        '''Only allow ConSys session channels'''
        if kind == CHANNEL_NAME:
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
    
#    def check_channel_subsystem_request(self, channel, name):
#        handler_class, larg, kwarg = \
#            channel.get_transport()._get_subsystem_handler(name)
#        if handler_class is None:
#            return False
#        handler = handler_class(channel, name, self, *larg, **kwarg)
#        scheduler.schedule(handler.run)
#        return True

class PersistentThreadingMixIn(object):
    '''A mix-in class for SocketServer, allows to create persistent
    connections asynchronously.
    '''

    def process_request_thread(self, request, client_address):
        '''Same as in BaseServer but as a thread.

        In addition, exception handling is done here.
        '''
        try:
            self.finish_request(request, client_address)
        except Exception: 
            self.handle_error(request, client_address)
            self.shutdown_request(request)

    def process_request(self, request, client_address):
        '''Start a new thread to process the request.'''
        t = threading.Thread(target = self.process_request_thread,
                             args = (request, client_address))
        t.setDaemon(1)
        t.start()
    
    def handle_error(self, request, client_address):
        '''Handle an error gracefully.'''
        _log.exception('Exception happened during processing of request '
                      'from \'{0}\''.format(client_address))

    
class SSHServer(AsyncMixIn, asyncore.dispatcher):
    '''An SSH protocol server.'''

    backlog_size = 5

    def __init__(self):
        '''Constructs a new server with specified configuration.'''
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((_config['bind-address'], _config['port']))
        self.listen(self.backlog_size)
        _log.debug('Server is listening on {0}:{1}'.format(_config['bind-address'],
                                                          _config['port']))
        self.server_pkey = \
            paramiko.RSAKey.from_private_key_file(_config['server-key'])
        self.client_key = load_public_key(_config['client-public-key'])
        self.username = _config['client-user-name']
        self.connections = []
        
    def handle_accept(self):
        '''Handles new incoming connections.'''
        client = self.accept()
        if client is None:
            return
        socket, client_address = client
        _log.debug('Incoming TCP connection '
                  'from {0}'.format(client_address))
        SSHConnection(socket, self)
    

def dispatch_loop():
    '''Dispatches messages until all dispatchers are closed.'''
    asyncore.loop()
