''' RPC common routines.

@author: Nikita Ofitserov
'''

from __future__ import unicode_literals 


class RPCException(Exception):
    ''' An RPC call failure. '''
    pass

class RPCEndpoint(object):
    ''' An RPC end-point -- either client or server. Allows service 
    registering and generic method calling. 
    '''

    def __init__(self):
        ''' Initializes an empty RPC end-point. '''
        self.services = {}
        
    def register_service(self, name, service):
        ''' Registers the specified service under given name. After this call
        all methods from the service object can be called remotely.
        '''
        self.services[name] = service
        
    def call_method(self, serviceName, methodName, args, kwargs):
        ''' Calls the specified service method, returning its result. If
        there is no such service or method, RPCException is thrown.  
        '''
        try:
            service = self.services[serviceName]
        except KeyError:
            raise RPCException('RPC service \'{0}\' is not '
                               'found'.format(serviceName))
        try:
            method = getattr(service, methodName)
        except AttributeError:
            raise RPCException('RPC method \'{0}\' on service \'{1}\' is '
                               'not found'.format(methodName, serviceName))
        return method(*args, **kwargs)
        
    