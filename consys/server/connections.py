''' Keeps track of network connections
@author: Nikita Ofitserov
'''
from twisted.spread import pb

class Tracker(pb.Referenceable):
    '''  '''
    def __init__(self):
        self.clients = []
        self.admins = []
        
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