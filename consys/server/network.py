'''
Server-side network routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals 

import logging
import socket
import SocketServer
import threading
import paramiko

from consys.common.network import load_public_key, CHANNEL_NAME, \
    CONTROL_SYBSYSTEM, RPC_C2S_SYBSYSTEM, RPC_S2C_SYBSYSTEM

__all__ = ['SSHServer']

log = logging.getLogger(__name__)

class ControlSubsystemHandler(paramiko.SubsystemHandler):
    '''
    Server-to-client control subsystem handler.
    '''
    def __init__(self, connection):
        self.connection = connection
    
    def start_subsystem(self, name, transport, channel):
        '''
        Request handling logic.
        '''
        log.debug("Incoming S2C control channel!")
        self.connection.set_control_channel(channel)

class RPCSubsystemHandler(paramiko.SubsystemHandler):
    '''
    Client-to-server RPC subsystem handler.
    '''
    def start_subsystem(self, name, transport, channel):
        '''
        Request handling logic.
        '''
        log.debug("Incoming C2S RPC channel!")
        
class RPCReverseSubsystemHandler(paramiko.SubsystemHandler):
    '''
    Server-to-client RPC subsystem handler.
    '''
    def start_subsystem(self, name, transport, channel):
        '''
        Request handling logic.
        '''
        log.debug("Incoming S2C RPC back-channel!")

class SSHConnection(object):
    '''
    A server side of the SSH connection.
    '''
    
    def __init__(self, socket, server):
        '''
        Creates a SSH server-side endpoint.
        '''
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
        '''
        Sets the control channel, if not already set.
        '''
        if self.control_channel is None:
            self.control_channel = channel
            
    def close(self):
        '''
        Closes the connection.
        '''
        # FIXME: clean up gracefully
        log.info("Closing SSH connection")
        self.transport.close()
        self.server.connections.remove(self)

class ServerImpl(paramiko.ServerInterface):
    '''
    A concrete ServerInterface implementation.
    '''
    
    def __init__(self, connection):
        self.connection = connection
        
    def get_allowed_auths(self, username):
        return b"publickey"
    
    def check_auth_publickey(self, username, key):
        server = self.connection.server
        if username == server.username and key == server.client_key:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED
    
    def check_channel_request(self, kind, chanid):
        """ Only allow ConSys session channels """
        if kind == CHANNEL_NAME:
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    
class SSHServer(SocketServer.TCPServer):
    '''
    A SSH protocol server.
    '''

    class TCPHandler(SocketServer.BaseRequestHandler):
        '''
        A simple incoming connection handler.
        '''        
        def handle(self):
            log.debug("Incoming TCP connection "
                      "from {0}".format(self.client_address))
            connection = None
            try:
                # self.request is the TCP socket
                # self.server is the TCPServer instance
                connection = SSHConnection(self.request, self.server)
                self.server.connections.append(connection)
            except socket.error:
                log.debug("Socket error, closing connection")
                if connection is not None:
                    connection.close();
            except Exception:
                log.exception('Unhandled exception in the TCP connection '
                              'handler')
                raise
    
    def __init__(self, config):
        '''
        Constructs a new server with specified configuration.
        '''
        SocketServer.TCPServer.__init__(self, (config[b"bind-address"],
                                               config[b"listen-port"]),
                                        SSHServer.TCPHandler)
        self.server_pkey = \
            paramiko.RSAKey.from_private_key_file(config[b"server-key"])
        self.client_key = load_public_key(config[b"client-public-key"])
        self.username = config[b"client-user-name"]
        self.connections = []
        