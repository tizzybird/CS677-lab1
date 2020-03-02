import xmlrpc
from xmlrpc.server import SimpleXMLRPCServer

# import json
import socket
import threading as thd
from threading import Lock

import random
import time

BUYER  = 1
SELLER = 2
BOTH   = 3

FISH = 11
SALT = 12
BOAR = 13
MAX_ITEM_NUMBER = 20

# ADDR = socket.gethostbyname(socket.gethostname())
PORT_START_NUM = 10070

PEER_NUM = 6
MAX_BUYER_NUM  = int(PEER_NUM/2) + 1
MAX_SELLER_NUM = int(PEER_NUM/2) + 1

LOCK_PRINT = Lock()

class Peer(thd.Thread):
    def __init__(self, peer_id, role):
        thd.Thread.__init__(self)
        
        self.peer_id = peer_id
        self.role = role
        
        # build neighbor list randomly
        self.neighbors = []
        for i in range(PEER_NUM):
            if i != peer_id and random.randint(0, 1) == 1:
                self.neighbors.append(i)
        
        if len(self.neighbors) == 0:
            self.neighbors.append(peer_id - 1 if peer_id > 0 else peer_id + 1)
            

    def run(self):
        server = thd.Thread(target=self.initiate_rpc_server)
        server.start()

        # if self.role == BUYER or self.role == BOTH:
        #     for i in self.neighbors:
        #         addr = "http://localhost:%d/" % (PORT_START_NUM+i)
        #         proxy = xmlrpc.client.ServerProxy(addr)
        #         with LOCK_PRINT:
        #             print ("-------------> Peer %d calls neighbor %d" % (self.peer_id, i))
                
        #         # testing
        #         if proxy.show_me_some_message(self.peer_id):
        #             with LOCK_PRINT:
        #                 print ("-------------- Peer %d finishes calling" % (self.peer_id))
        
        server.join()


    def initiate_buyer(self):
        # generate a buy request
        self.target = random.randint(FISH, BOAR)
        if self.role == BOTH:
            while self.target == self.commodity:
                self.target = random.randint(FISH, BOAR)
        
        self.target_quantity = random.randint(1, MAX_ITEM_NUMBER)
        self.timeout = random.randint(3, 9)

        for neighbor_id in self.neighbors:
            addr = "http://localhost:%d/" % (PORT_START_NUM+neighbor_id)
            proxy = xmlrpc.client.ServerProxy(addr)
            proxy.lookup(self.target, self.timeout, '%d' % self.peer_id)


    def initiate_seller(self):
        self.commodity = random.randint(FISH, BOAR)
        self.commodity_number = random.randint(1, MAX_ITEM_NUMBER)

    
    # for testing
    # def show_test_message(self, from_id):
    #     with LOCK_PRINT:
    #         print ("<------------- Peer %d receives a call from %s" % (self.peer_id, from_id))

    #     return True


    def initiate_rpc_server(self):
        with LOCK_PRINT:
            print("The server of peer %d is running" % self.peer_id)
        server = SimpleXMLRPCServer(("localhost", PORT_START_NUM + self.peer_id))
        server.register_function(self.lookup)
        server.register_function(self.reply)

        if self.role != SELLER:
            server.register_function(self.buy)
        # server.register_function(self.show_test_message)
        server.serve_forever()


    def lookup(self, product_name, hopcount, path):
        footprints = path.split('-')
        if self.role == BUYER:
            # discard
            if hopcount == 0:
                return False

            for neighbor_id in self.neighbors:
                if str(neighbor_id) not in footprints:
                    addr = "http://localhost:%d/" % (PORT_START_NUM + neighbor_id)
                    proxy = xmlrpc.client.ServerProxy(addr)
                    proxy.lookup(product_name, hopcount-1, "%d-%s" % (self.peer_id, path))

            return True


        if product_name == self.commodity:
            # lock here in case that a traction proceeds while a message saying that
            # the seller has the item is on the road
            from_neighbor_id = int(footprints[0])
            new_path = "-".join(footprints[1:])
            
            addr = "http://localhost:%d/" % (PORT_START_NUM + from_neighbor_id)
            proxy = xmlrpc.client.ServerProxy(addr)
            proxy.reply(self.peer_id, new_path)


    def reply(self, seller_id, path):
        footprints = path.split('-')
        from_neighbor_id = int(footprints[0])

        # buy, TODO what if there are multiple reply?
        if from_neighbor_id == self.peer_id:
            addr = "http://localhost:%d/" % (PORT_START_NUM + seller_id)
            proxy = xmlrpc.client.ServerProxy(addr)
            # fail
            result = proxy.buy(self.target, self.target_quantity)
            if result == -1:
                pass
            
            self.target_quantity -= result
            
            # TODO: regenerate a buy request
            if self.target_quantity == 0:
                pass

            return True

        new_path = "-".join(footprints[1:])
        
        addr = "http://localhost:%d/" % (PORT_START_NUM + from_neighbor_id)
        proxy = xmlrpc.client.ServerProxy(addr)
        proxy.reply(self.peer_id, new_path)

        return True


    def buy(self, product_name, quantity):
        # TODO get the lock first?
        if product_name != self.commodity:
            return -1
        
        # TODO should generate a new commodity to sell
        if self.commodity_number <= quantity:
            return self.commodity_number
        
        self.commodity_number -= quantity
        return quantity


if __name__ == "__main__":
    # Use one main thread to generate other threads that
    # run as peers
    buyer_num  = 0
    seller_num = 0
    peers = []
    # ensure that there is always a buyer and a seller
    for i in range(PEER_NUM):
        while True:
            role = random.randint(BUYER, BOTH)
            if role == BUYER and buyer_num <= MAX_BUYER_NUM:
                buyer_num += 1
                break
            elif role == SELLER and seller_num <= MAX_SELLER_NUM:
                seller_num += 1
                break
            elif role == BOTH:
                buyer_num += 1
                seller_num += 1
                break

        peers.append(Peer(i, role))
        peers[i].start()

    # avoid closing main thread
    for peer in peers:
        peer.join()
