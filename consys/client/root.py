''' RPC root object for the client
@author: Nikita Ofitserov
'''
from twisted.spread import pb
from twisted.internet import reactor

class Root(pb.Referenceable):
    
    def remote_shutdown(self):
        reactor.stop()
