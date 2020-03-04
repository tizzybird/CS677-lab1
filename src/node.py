import xmlrpc
from xmlrpc.server import SimpleXMLRPCServer

# import json
import socket
import threading as thd
from threading import Lock

import random
import time

DEBUG = False

BUYER  = 1
SELLER = 2
BOTH   = 3

FISH = 11
SALT = 12
BOAR = 13
MAX_ITEM_NUMBER = 10
TO_ITEM_NAME = {
    FISH: 'fish',
    SALT: 'salt',
    BOAR: 'boar'
}

ADDR = "http://localhost:%d/"
PORT_START_NUM = 10070

CLIENT_TIMEOUT = 8

PEER_NUM = 6
MAX_BUYER_NUM  = int(PEER_NUM/2) + 1
MAX_SELLER_NUM = int(PEER_NUM/2) + 1

PRINT_LOCK = False or Lock()

class Peer(thd.Thread):
    def __init__(self, peer_id, role, neighbors):
        thd.Thread.__init__(self)
        
        self.peer_id = peer_id
        self.role = role
        self.neighbors = neighbors

        with PRINT_LOCK:
            print("[Neighbor] Neighbors of peer %d: %s" % (self.peer_id, ','.join(str(x) for x in self.neighbors)))
            

    def run(self):
        server = thd.Thread(target=self._initiate_rpc_server)
        server.start()
        
        if self.role == SELLER or self.role == BOTH:
            self._initiate_seller()
        
        if self.role == BUYER or self.role == BOTH:
            self._initiate_buyer()

        server.join()


    def _initiate_buyer(self):
        # with PRINT_LOCK:
        #     print("[INIT] Peer %d is a buyer" % self.peer_id)

        while True:
            time.sleep(3)
            # generate a buy request
            self.target = random.randint(FISH, BOAR)
            # make sure that the target is different with commodity
            if self.role == BOTH:
                while self.target == self.commodity:
                    self.target = random.randint(FISH, BOAR)
            
            with PRINT_LOCK:
                print("[Generate] Peer %d plans to buy %s" % (self.peer_id, TO_ITEM_NAME[self.target]))
        
            self.candidate_sellers = []
            for neighbor_id in self.neighbors:
                addr = ADDR % (PORT_START_NUM + neighbor_id)
                # proxy = xmlrpc.client.ServerProxy(addr)
                proxy = self._get_proxy(addr)
                if proxy != None:
                    proxy.lookup(self.target, CLIENT_TIMEOUT, '%d' % self.peer_id)

            with PRINT_LOCK:
                print("[Rest] Peer %d waits for %d seconds" % (self.peer_id, CLIENT_TIMEOUT))
            
            time.sleep(CLIENT_TIMEOUT)
            
            # transaction
            for seller_id in self.candidate_sellers:
                addr = ADDR % (PORT_START_NUM + seller_id)
                proxy = self._get_proxy(addr)
                # proxy = xmlrpc.client.ServerProxy(addr)
                if proxy != None and proxy.buy(self.target):
                    with PRINT_LOCK:
                        print("[SUCCESS] Peer %d buys %s from seller %d" % (self.peer_id, TO_ITEM_NAME[self.target], seller_id))
                    break


    def _initiate_seller(self):
        # with PRINT_LOCK:
        #     print("[INIT] Peer %d is a seller" % self.peer_id)

        self.commodity = random.randint(FISH, BOAR)
        self.commodity_quantity = random.randint(1, MAX_ITEM_NUMBER)
        self.commodity_lock = Lock()

        with PRINT_LOCK:
            print("[Generate] Peer %d sells %d number of %s" %
                (self.peer_id, self.commodity_quantity, TO_ITEM_NAME[self.commodity]))

    
    # for testing
    # def show_test_message(self, from_id):
    #     with PRINT_LOCK:
    #         print ("<------------- Peer %d receives a call from %s" % (self.peer_id, from_id))

    #     return True


    def _initiate_rpc_server(self):
        
        server = SimpleXMLRPCServer(("localhost", PORT_START_NUM + self.peer_id),
                    allow_none=True, logRequests=False)

        server.register_function(self.lookup)
        server.register_function(self.reply)

        # Clients don't have to listen to buy requests
        if self.role != BUYER:
            server.register_function(self.buy)
        
        # server.register_function(self.show_test_message)
        server.serve_forever()

    
    def _get_proxy(self, addr):
        proxy = xmlrpc.client.ServerProxy(addr)
        try:
            proxy.test()   # Call a fictive method.
        except xmlrpc.client.Fault:
            # connected to the server and the method doesn't exist which is expected.
            pass
        except socket.error:
            # Not connected ; socket error mean that the service is unreachable.
            return None
            
        # Just in case the method is registered in the XmlRPC server
        return proxy

    # Helper Method: Send Lookup Request to the Neighbor.
    def _lookup(self, addr, product_name, hopcount, path):
        # Lookup Neighbor.
        proxy = self._get_proxy(addr)
        if proxy != None:
            # Just in case the method is registered in the XmlRPC server
            proxy.lookup(product_name, hopcount, path)

    def _reply(self, addr, seller_id, new_path):
        proxy = self._get_proxy(addr)
        if proxy != None:
            proxy.reply(seller_id, new_path)
  

    def lookup(self, product_name, hopcount, path):
        footprints = path.split('-')
        
        # have the product
        if self.role != BUYER and product_name == self.commodity:
            from_neighbor_id = int(footprints[0])
            new_path = '' if len(footprints) == 1 else "-".join(footprints[1:])

            addr = ADDR % (PORT_START_NUM + from_neighbor_id)
            # proxy = xmlrpc.client.ServerProxy(addr)
            proxy = self._get_proxy(addr)
            if proxy != None:
                with PRINT_LOCK:
                    print("Peer %d has %s!, reply to %d" % (self.peer_id,
                        TO_ITEM_NAME[product_name], from_neighbor_id))
                proxy.reply(self.peer_id, new_path)

            return True

        # discard
        if hopcount == 0:
            with PRINT_LOCK:
                print("[LOOKUP stop] Peer %d final path: %s" % (self.peer_id, path))
            return False

        # propagate the request
        for neighbor_id in self.neighbors:
            if str(neighbor_id) not in footprints:
                addr = ADDR % (PORT_START_NUM + neighbor_id)
                new_path = "%d-%s" % (self.peer_id, path)
                thread = thd.Thread(target=self._lookup, args=(addr, product_name, hopcount-1, new_path))
                thread.start()
                # proxy = xmlrpc.client.ServerProxy(addr)
                # proxy.lookup(product_name, hopcount-1, "%d-%s" % (self.peer_id, path))
                with PRINT_LOCK:
                    print("[LOOKUP propagate] Peer %d: %d <- %s" % (self.peer_id, neighbor_id, new_path))

        return True


    def reply(self, seller_id, path):
        # 1. The reply request arrives to the client
        if len(path) == 0:
            with PRINT_LOCK:
                print("[RECEIVE] Buyer %d receives a reply from seller %d" % (self.peer_id, seller_id))
            self.candidate_sellers.append(seller_id)
            return True
        
        # 2. Otherwise, propagate the reply request
        footprints = path.split('-')
        next_neighbor_id = int(footprints[0])
        new_path = '' if len(footprints) == 1 else "-".join(footprints[1:])
        addr = ADDR % (PORT_START_NUM + next_neighbor_id)
        # proxy = self._get_proxy(addr)
        thread = thd.Thread(target=self._reply, args=(addr, seller_id, new_path))
        thread.start()
        # proxy = xmlrpc.client.ServerProxy(addr)
        # proxy.reply(seller_id, new_path)

        with PRINT_LOCK:
            print("[REPLY propagate] Peer %d -> %d - %s" % (self.peer_id, next_neighbor_id, new_path))

        return True


    def buy(self, product_name):
        if product_name != self.commodity:
            with PRINT_LOCK:
                print("[FAILURE] The %s of peer %d has been sold out." %
                    (TO_ITEM_NAME[self.commodity], self.peer_id))
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

        with PRINT_LOCK:
            print("[UPDATE] Seller %d has %d of %s to sell" % (self.peer_id,
                self.commodity_quantity, TO_ITEM_NAME[self.commodity]))

        return True


def generate_neighbor_map():
    neighbor_map = []
    for j in range(PEER_NUM):
        row = [False for i in range(PEER_NUM)]
        neighbor_map.append(row)

    # generate neighbor map
    for j in range(PEER_NUM):
        # make sure that a peer always has a neighbor
        assured = random.randint(0, j-1) if j == PEER_NUM-1 else random.randint(j+1, PEER_NUM-1)
        neighbor_map[j][assured] = True
        neighbor_map[assured][j] = True

        for i in range(j+1, PEER_NUM-1):
            if random.randint(0, 1) == 1:
                neighbor_map[j][i] = True
                neighbor_map[i][j] = True

    return neighbor_map


test_map1 = [
    [False, True, False],
    [True, False, True],
    [False, True, False]
]
test_role1 = [BUYER, SELLER, SELLER]

test_map2 = [
    [False, True, False, True],
    [True, False, True, False],
    [False, True, False, True],
    [True, False, True, False]
]
test_role2 = [BUYER, SELLER, SELLER, BOTH]

if __name__ == "__main__":
    # Use one main thread to generate other threads that run as peers
    buyer_num  = 0
    seller_num = 0
    peers = []

    if DEBUG:
        neighbor_map = test_map2

        with PRINT_LOCK:
            print('\\\\\\\\\\NEIGHBOR MAP://///')
            for row in neighbor_map:
                print(row)
            print('\n')

        for i in range(PEER_NUM):
            neighbors = []
            for j in range(PEER_NUM):
                if neighbor_map[i][j]:
                    neighbors.append(j)

            peers.append(Peer(i, test_role2[i], neighbors))
            peers[i].start()

    else:
        neighbor_map = generate_neighbor_map()

        with PRINT_LOCK:
            print('\\\\\\\\\\NEIGHBOR MAP://///')
            for row in neighbor_map:
                print(row)
            print('\n')

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
            
            neighbors = []
            for j in range(PEER_NUM):
                if neighbor_map[i][j]:
                    neighbors.append(j)

            peers.append(Peer(i, role, neighbors))
            peers[i].start()

    # avoid closing main thread
    for peer in peers:
        peer.join()