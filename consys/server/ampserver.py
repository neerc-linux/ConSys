'''
AMP server-side client.
@author: Nikita Ofitserov
'''
from twisted.protocols import amp
from twisted.internet import protocol

class AmpServerProtocol(amp.AMP):
    pass

factory = protocol.Factory() 
factory.protocol = AmpServerProtocol
  
