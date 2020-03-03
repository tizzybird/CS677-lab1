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

ADDR = "http://localhost:%d/"
PORT_START_NUM = 10070

CLIENT_TIMEOUT = 8

PEER_NUM = 4
MAX_BUYER_NUM  = int(PEER_NUM/2) + 1
MAX_SELLER_NUM = int(PEER_NUM/2) + 1

PRINT_LOCK = Lock()

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
        
        # make sure that a peer has at least a neighbor
        if len(self.neighbors) == 0:
            self.neighbors.append((peer_id - 1) if peer_id > 0 else (peer_id + 1))
            

    def run(self):
        server = thd.Thread(target=self.initiate_rpc_server)
        server.start()
        
        if self.role == SELLER or self.role == BOTH:
            self.initiate_seller()
        
        if self.role == BUYER or self.role == BOTH:
            self.initiate_buyer()

        server.join()


    def initiate_buyer(self):
        while True:
            time.sleep(3)
            # generate a buy request
            self.target = random.randint(FISH, BOAR)
            # make sure that the target is different with commodity
            if self.role == BOTH:
                while self.target == self.commodity:
                    self.target = random.randint(FISH, BOAR)
            
            # self.target_quantity = random.randint(1, MAX_ITEM_NUMBER)
            # self.timeout = random.randint(3, 9)
            with PRINT_LOCK:
                print("Peer %d is a buyer, target: %d" % (self.peer_id, self.target))
        
            self.candidate_sellers = []
            for neighbor_id in self.neighbors:
                addr = ADDR % (PORT_START_NUM + neighbor_id)
                proxy = xmlrpc.client.ServerProxy(addr)
                proxy.lookup(self.target, CLIENT_TIMEOUT, '%d' % self.peer_id)

            time.sleep(CLIENT_TIMEOUT)

            # transaction
            for seller_id in self.candidate_sellers:
                addr = ADDR % (PORT_START_NUM + seller_id)
                proxy = xmlrpc.client.ServerProxy(addr)
                if proxy.buy(self.target):
                    with PRINT_LOCK:
                        print("[SUCCESS] Peer %d buys %d from peer %d" % (self.peer_id, self.target, seller_id))
                    break


    def initiate_seller(self):
        self.commodity = random.randint(FISH, BOAR)
        self.commodity_quantity = random.randint(1, MAX_ITEM_NUMBER)
        # self.commodity_quantity = random.randint(1, MAX_ITEM_NUMBER)
        self.commodity_lock = Lock()

        with PRINT_LOCK:
            print("Peer %d is a seller, commodity: %d" % (self.peer_id, self.commodity))

    
    # for testing
    # def show_test_message(self, from_id):
    #     with PRINT_LOCK:
    #         print ("<------------- Peer %d receives a call from %s" % (self.peer_id, from_id))

    #     return True


    def initiate_rpc_server(self):
        # with PRINT_LOCK:
        #     print("The server of peer %d is running" % self.peer_id)
        
        server = SimpleXMLRPCServer(("localhost", PORT_START_NUM + self.peer_id), allow_none=True, logRequests=False)
        server.register_function(self.lookup)
        server.register_function(self.reply)

        # Clients don't have to listen to buy requests
        if self.role != BUYER:
            server.register_function(self.buy)
        
        # server.register_function(self.show_test_message)
        server.serve_forever()


    def lookup(self, product_name, hopcount, path):
        footprints = path.split('-')
        with PRINT_LOCK:
            print("Peer %d receives lookup request of product %d, path: %s" % (self.peer_id, product_name, path))
        # have the product
        if self.role != BUYER and product_name == self.commodity:
            from_neighbor_id = int(footprints[0])
            new_path = "-".join(footprints[1:])
            
            with PRINT_LOCK:
                print("Peer %d has %d!, reply to %d" % (self.peer_id, product_name, from_neighbor_id))

            addr = ADDR % (PORT_START_NUM + from_neighbor_id)
            proxy = xmlrpc.client.ServerProxy(addr)
            proxy.reply(self.peer_id, new_path)

            return True

        # discard
        if hopcount == 0:
            return False

        # propagate the request
        for neighbor_id in self.neighbors:
            if str(neighbor_id) not in footprints:
                addr = ADDR % (PORT_START_NUM + neighbor_id)
                proxy = xmlrpc.client.ServerProxy(addr)
                proxy.lookup(product_name, hopcount-1, "%d-%s" % (self.peer_id, path))
                with PRINT_LOCK:
                    print("------> Peer %d propagates LOOKUP request to its neighbor %d" % (self.peer_id, neighbor_id))

        return True


    def reply(self, seller_id, path):
        # 1. The reply request arrives to the client
        if len(path) == 0:
            with PRINT_LOCK:
                print("[RECEIVE] Peer %d receives a reply from peer %d" % (self.peer_id, seller_id))
            self.candidate_sellers.append(seller_id)
            return True

        # 2. Otherwise, propagate the reply request
        footprints = path.split('-')
        next_neighbor_id = int(footprints[0])
        new_path = '' if len(footprints) == 1 else "-".join(footprints[1:])
        addr = ADDR % (PORT_START_NUM + next_neighbor_id)
        proxy = xmlrpc.client.ServerProxy(addr)
        proxy.reply(seller_id, new_path)

        with PRINT_LOCK:
            print("------> Peer %d propagates REPLY request to %d" % (self.peer_id, next_neighbor_id))

        return True


    def buy(self, product_name):
        if product_name != self.commodity:
            with PRINT_LOCK:
                print("[FAILURE] Commodity %d of %d has been sold out." % (self.commodity, self.peer_id))
            return False

        # sync
        with self.commodity_lock:
            if self.commodity_quantity <= 0:
                return False

            self.commodity_quantity -= 1
        
            if self.commodity_quantity == 0:
                self.commodity_quantity = random.randint(1, MAX_ITEM_NUMBER)
                self.commodity = random.randint(FISH, BOAR)
                if self.role == BOTH:
                    while self.commodity == self.target:
                        self.commodity = random.randint(FISH, BOAR)
                
        return True


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
