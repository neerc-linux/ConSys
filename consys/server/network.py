'''Server-side network routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals 

import logging
import socket
import asyncore
import threading
import paramiko

from consys.common.network import load_public_key, CHANNEL_NAME, \
    CONTROL_SYBSYSTEM, RPC_C2S_SYBSYSTEM, RPC_S2C_SYBSYSTEM
import consys.common.config as conf

__all__ = ['SSHServer']

config = conf.registerSection('network', {
                                          'bind-address': 'string(default=0.0.0.0)',
                                          'port': 'integer(min=1, max=65535, default=2222)',
                                          'server-key': 'string(default=/etc/consys/keys/server)',
                                          'client-public-key': 'string(default=/etc/consys/keys/client.pub)',
                                          'client-user-name': 'string(default=test)',
                                          })
log = logging.getLogger(__name__)

class ControlSubsystemHandler(paramiko.SubsystemHandler):
    '''Server-to-client control subsystem handler.'''
    
    def __init__(self, channel, name, server, connection):
        paramiko.SubsystemHandler.__init__(self, channel, name, server)
        self.connection = connection
    
    def start_subsystem(self, name, transport, channel):
        '''Request handling logic.'''
        log.debug("Incoming S2C control channel!")
        self.connection.set_control_channel(channel)
        import pdb; pdb.set_trace()
        channel.sendall(b'WTF?')

class RPCSubsystemHandler(paramiko.SubsystemHandler):
    '''Client-to-server RPC subsystem handler.'''
    
    def start_subsystem(self, name, transport, channel):
        '''Request handling logic.'''
        log.debug("Incoming C2S RPC channel!")
        
class RPCReverseSubsystemHandler(paramiko.SubsystemHandler):
    '''Server-to-client RPC subsystem handler.'''
    
    def start_subsystem(self, name, transport, channel):
        '''Request handling logic.'''
        log.debug("Incoming S2C RPC back-channel!")

class SSHConnection(object):
    '''A server side of the SSH connection.'''
    
    def __init__(self, socket, server):
        '''Creates a SSH server-side endpoint.'''
        self.server = server
        self.transport = paramiko.Transport(socket)
        self.transport.add_server_key(server.server_pkey)
        self.transport.start_server(server=ServerImpl(self))
        self.transport.set_subsystem_handler(CONTROL_SYBSYSTEM, 
                                             ControlSubsystemHandler, self)
        self.transport.set_subsystem_handler(RPC_C2S_SYBSYSTEM, 
                                             RPCSubsystemHandler)
        self.control_channel = None
        
    def set_control_channel(self, channel):
        '''Sets the control channel, if not already set.'''
        if self.control_channel is None:
            self.control_channel = channel
            
    def close(self):
        '''Closes the connection.'''
        # FIXME: clean up gracefully
        log.info("Closing SSH connection")
        self.transport.close()
        self.server.connections.remove(self)
        
        
class ServerImpl(paramiko.ServerInterface):
    '''A concrete ServerInterface implementation.'''
    
    def __init__(self, connection):
        self.connection = connection
        
    def handle_disconnect(self):
        self.connection.close()
        
    def get_allowed_auths(self, username):
        return b"publickey"
    
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
        log.exception('Exception happened during processing of request '
                      'from "{0}"'.format(client_address))

    
class SSHServer(asyncore.dispatcher):
    '''An SSH protocol server.'''

    backlog_size = 5

    def __init__(self):
        '''Constructs a new server with specified configuration.'''
        self.map = {}
        asyncore.dispatcher.__init__(self, map=self.map)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((config['bind-address'], config['port']))
        self.listen(self.backlog_size)
        log.debug('Server is listening on {0}:{1}'.format(config['bind-address'],
                                                          config['port']))
        self.server_pkey = \
            paramiko.RSAKey.from_private_key_file(config['server-key'])
        self.client_key = load_public_key(config['client-public-key'])
        self.username = config['client-user-name']
        self.connections = []
        
    def handle_accept(self):
        '''Handles new incoming connections.'''
        client = self.accept()
        if client is None:
            return
        socket, client_address = client
        log.debug('Incoming TCP connection '
                  'from {0}'.format(client_address))
        connection = SSHConnection(socket, self)
        self.connections.append(connection)
    
    def serve_forever(self):
        '''Serves until this server is closed.'''
        asyncore.loop(map=self.map)
