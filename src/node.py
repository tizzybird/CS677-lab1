import xmlrpc
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

import socket
import threading as thd
from threading import Lock

import random
import time, datetime

import logging

from define import *

# logging.basicConfig(level=logging.INFO)
PRINT_LOCK = Lock()

class Peer(thd.Thread):
    def __init__(self, peer_id, role, neighbors):
        thd.Thread.__init__(self)
        
        self.peer_id = peer_id
        self.role = role
        self.neighbors = neighbors
        self.latency = 0
        self.request_count = 0

        with PRINT_LOCK:
            print("[Neighbor] Neighbors of peer %d: %s" % (self.peer_id, ','.join(str(x) for x in self.neighbors)))
            
    # entry point
    def run(self):
        server = thd.Thread(target=self._initiate_rpc_server)
        server.start()
        
        if self.role == SELLER or self.role == BOTH:
            self._initiate_seller()
        
        if self.role == BUYER or self.role == BOTH:
            self._initiate_buyer()

        while True:
            try:
                server.join()
            except RuntimeError:
                with PRINT_LOCK:
                    print("The rpc server of peer %d is down, reinitiate..." % self.peer_id)
                
                server = thd.Thread(target=self._initiate_rpc_server)
                server.start()


    def _initiate_buyer(self):
        while True:
            time.sleep(3)
            # generate a buy request
            self.target = random.randint(FISH, BOAR)
            # make sure that the target is different with commodity
            if self.role == BOTH:
                while self.target == self.commodity:
                    self.target = random.randint(FISH, BOAR)
            
            with PRINT_LOCK:
                print("[INIT] Peer %d plans to buy %s" % (self.peer_id, TO_ITEM_NAME[self.target]))
            
            self.candidate_sellers = []
            for neighbor_id in self.neighbors:
                proxy = self._get_proxy(neighbor_id)
                if proxy != None:
                    t_start = datetime.datetime.now()
                    proxy.lookup(self.target, HOPCOUNT, '%d' % self.peer_id)
                    t_stop = datetime.datetime.now()
                    self.latency += (t_stop - t_start).total_seconds()
                    self.request_count += 1
                    self._report_performance()


            time.sleep(CLIENT_TIMEOUT)
            
            # transaction
            for seller_id in self.candidate_sellers:
                proxy = self._get_proxy(seller_id)
                if proxy != None and proxy.buy(self.target):
                    with PRINT_LOCK:
                        print("[SUCCESS] Peer %d buys %s from peer %d" % (self.peer_id, TO_ITEM_NAME[self.target], seller_id))
                    break


    def _initiate_seller(self):
        self.commodity = random.randint(FISH, BOAR)
        self.commodity_quantity = random.randint(1, MAX_ITEM_NUMBER)
        self.commodity_lock = Lock()

        with PRINT_LOCK:
            print("[INIT] Peer %d sells %d number of %s" %
                (self.peer_id, self.commodity_quantity, TO_ITEM_NAME[self.commodity]))


    def _report_performance(self):
        if self.request_count % 50 != 0:
            return
        
        with PRINT_LOCK:
            print('**** [PERFORMANCE] Average latency of peer %d: %f (sec/req) ****' %
                (self.peer_id, (self.latency / self.request_count)))


    def _initiate_rpc_server(self):
        if SCENARIO == 1:
            host_ip = "localhost"
        else:
            host_ip = socket.gethostbyname(socket.gethostname())

        server = SimpleXMLRPCServer((host_ip, PORT_START_NUM + self.peer_id),
                    allow_none=True, logRequests=False)

        server.register_function(self.lookup)
        server.register_function(self.reply)

        # Clients don't have to listen to buy requests
        if self.role != BUYER:
            server.register_function(self.buy)
        
        # server.register_function(self.show_test_message)
        server.serve_forever()

    def _get_proxy(self, peer_id):
        if SCENARIO == 1:
            addr = ADDR % (PORT_START_NUM + peer_id)
        elif peer_id in MASTER_PEER_ID:
            addr = MASTER_ADDR % (PORT_START_NUM + peer_id)
        else:
            addr = SLAVE_ADDR % (PORT_START_NUM + peer_id)

        proxy = xmlrpc.client.ServerProxy(addr)

        try:
            proxy.test()   # call a fictive method.
        except xmlrpc.client.Fault:
            pass
        except socket.error:    # service is unreachable.
            return None
            
        return proxy

    # for thread to execute
    def _lookup(self, peer_id, product_name, hopcount, path):
        proxy = self._get_proxy(peer_id)
        if proxy != None:
            proxy.lookup(product_name, hopcount, path)

    # for thread to execute
    def _reply(self, peer_id, seller_id, new_path):
        proxy = self._get_proxy(peer_id)
        if proxy != None:
            proxy.reply(seller_id, new_path)
  

    def lookup(self, product_name, hopcount, path):
        footprints = path.split('-')
        
        # have the product
        if self.role != BUYER and product_name == self.commodity:
            from_neighbor_id = int(footprints[0])
            new_path = '' if len(footprints) == 1 else "-".join(footprints[1:])

            proxy = self._get_proxy(from_neighbor_id)
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
                new_path = "%d-%s" % (self.peer_id, path)
                t_start = datetime.datetime.now()
                thread = thd.Thread(target=self._lookup,
                    args=(neighbor_id, product_name, hopcount-1, new_path))
                thread.start()
                t_stop = datetime.datetime.now()
                self.latency += (t_stop - t_start).total_seconds()
                self.request_count += 1
                self._report_performance()
                with PRINT_LOCK:
                    print("[LOOKUP propagate] Peer %d: (next) %d <- %s (path)" % (self.peer_id, neighbor_id, new_path))

        return True


    def reply(self, seller_id, path):
        # 1. The reply request arrives to the client
        if len(path) == 0:
            self.candidate_sellers.append(seller_id)

            with PRINT_LOCK:
                print("[RECEIVE] Peer %d receives a reply from peer %d" % (self.peer_id, seller_id))
            
            return True
        
        # 2. Otherwise, propagate the reply request
        footprints = path.split('-')
        next_neighbor_id = int(footprints[0])
        new_path = '' if len(footprints) == 1 else "-".join(footprints[1:])

        t_start = datetime.datetime.now()
        thread = thd.Thread(target=self._reply, args=(next_neighbor_id, seller_id, new_path))
        thread.start()
        t_stop = datetime.datetime.now()
        self.latency += (t_stop - t_start).total_seconds()
        self.request_count += 1
        self._report_performance()

        with PRINT_LOCK:
            print("[REPLY propagate] from peer %d -> %d -%s (path)" % (self.peer_id, next_neighbor_id, new_path))

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
            print("[UPDATE] Peer %d has %d %s to sell" % (self.peer_id,
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


def one_machine_scenario():
    # Use one main thread to generate other threads that run as peers
    neighbor_map = test_map
    PEER_NUM = len(neighbor_map)
    role = test_role

    """
    # DEPRECATED
    if DEBUG:
        neighbor_map = test_map
        PEER_NUM = len(neighbor_map)
        role = test_role
    else:
        neighbor_map = generate_neighbor_map()
        buyer_num  = 0
        seller_num = 0
        role = []

        for i in range(PEER_NUM):
            tmp = BUYER
            while True:
                tmp = random.randint(BUYER, BOTH)
                if tmp == BUYER and buyer_num <= MAX_BUYER_NUM:
                    buyer_num += 1
                    break
                elif tmp == SELLER and seller_num <= MAX_SELLER_NUM:
                    seller_num += 1
                    break
                elif tmp == BOTH:
                    buyer_num += 1
                    seller_num += 1
                    break
            role.append(tmp)
    """
    
    with PRINT_LOCK:
        print('\\\\\\\\\\  *NEIGHBOR MAP*  /////')
        for row in neighbor_map:
            print(row)
        print('\n')

    peers = []
    for i in range(PEER_NUM):
        neighbors = []
        for j in range(PEER_NUM):
            if neighbor_map[i][j]:
                neighbors.append(j)

        peers.append(Peer(i, role[i], neighbors))
        peers[i].start()

    # avoid closing main thread
    for peer in peers:
        peer.join()


if __name__ == "__main__":
    # 1. For the scenario that test on a single machine
    if SCENARIO == 1:
        one_machine_scenario()

    # 2. For the scenario that test on two machines
    if SCENARIO == 2:
        # only support self-defined neighbor map
        neighbor_map = test_map
        PEER_NUM = len(neighbor_map)
        role = test_role
        host_ip = socket.gethostbyname(socket.gethostname())

        with PRINT_LOCK:
            print('Node is running on: %s\n' % host_ip)
            print('\\\\\\\\\\  *NEIGHBOR MAP*  /////')
            for row in neighbor_map:
                print(row)
            print('\n')

        curr_machine_peer_id = MASTER_PEER_ID if host_ip == MASTER_IP else SLAVE_PEER_ID
        peers = []
        for peer_id in curr_machine_peer_id:
            neighbors = []
            for j in range(PEER_NUM):
                if neighbor_map[peer_id][j]:
                    neighbors.append(j)

            peer = Peer(peer_id, role[peer_id], neighbors)
            peers.append(peer)
            peer.start()

        # avoid closing main thread
        for peer in peers:
            peer.join()
