''' Keeps track of network connections
@author: Nikita Ofitserov
'''

from twisted.spread import pb

from consys.server import log
from consys.server import network

_log = log.getLogger(__name__)

class Tracker(pb.Referenceable):
    '''  '''
    def __init__(self):
        self.clients = []
        self.admins = []
        network.client_connected.connect(self.added_client)
        network.client_disconnected.connect(self.removed_client)
        
    def added_client(self, avatar):
        self.clients.append(avatar)

    def added_admin(self, avatar):
        self.admins.append(avatar)

    def removed_client(self, avatar):
        self.clients.remove(avatar)

    def removed_admin(self, avatar):
        self.clients.remove(avatar)
    
    def get_clients(self):
        return self.clients
    
    def get_admins(self):
        return self.admins
    
tracker = Tracker()
