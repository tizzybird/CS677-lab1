import xmlrpc
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

import socket
import threading as thd
from threading import Lock

import random
import time, datetime

import logging

from define import *


PRINT_LOCK = Lock()
PROXY_ADDR_LIST = []
CURR_IP = 'localhost' if LOCAL_DEPLOY else socket.gethostbyname(socket.gethostname())

class Peer(thd.Thread):
    def __init__(self, peer_id, role, neighbors):
        thd.Thread.__init__(self)
        
        self.peer_id = peer_id
        self.role = role
        self.neighbors = neighbors
        self.latency = 0
        self.request_count = 0

        self._print("[Neighbor] Neighbors of peer %d: %s",
            (self.peer_id, ','.join(str(x) for x in self.neighbors)))
            
    # entry point
    def run(self):
        server = thd.Thread(target=self._initiate_rpc_server)
        server.start()
        
        if self.role == SELLER or self.role == BOTH:
            self._initiate_seller()
        
        if self.role == BUYER or self.role == BOTH:
            self._initiate_buyer()


    def _initiate_buyer(self):
        while True:
            time.sleep(3)
            # generate a buy request
            self.target = random.randint(FISH, BOAR)
            # make sure that the target is different with commodity
            if self.role == BOTH:
                while self.target == self.commodity:
                    self.target = random.randint(FISH, BOAR)
            
            self._print("[INIT] Peer %d plans to buy %s", (self.peer_id, TO_ITEM_NAME[self.target]))
            self.t_buy = datetime.datetime.now()
            self.response_time = 0

            # ask neighbors
            self.candidate_sellers = []
            for neighbor_id in self.neighbors:
                thread = thd.Thread(target=self._lookup_t,
                    args=(neighbor_id, self.target, HOPCOUNT, '%d' % self.peer_id))
                thread.start()

            time.sleep(CLIENT_TIMEOUT)
            
            # check candidate sellers and trade
            for seller_id in self.candidate_sellers:
                proxy = self._get_proxy(seller_id)
                if proxy != None and proxy.buy(self.target):
                    self._print("[SUCCESS] Peer %d buys %s from peer %d; avg. response time: %f (sec/req)",
                        (self.peer_id, TO_ITEM_NAME[self.target], seller_id,
                        (self.response_time / len(self.candidate_sellers))))
                    break
                

    def _initiate_seller(self):
        self.commodity = random.randint(FISH, BOAR)
        self.commodity_quantity = random.randint(1, MAX_ITEM_NUMBER)
        self.commodity_lock = Lock()

        self._print("[INIT] Peer %d sells %d units of %s",
            (self.peer_id, self.commodity_quantity, TO_ITEM_NAME[self.commodity]))


    def _initiate_rpc_server(self):
        server = SimpleXMLRPCServer((CURR_IP, PORT_START_NUM + self.peer_id),
                    allow_none=True, logRequests=False)

        server.register_function(self.hello)
        server.register_function(self.lookup)
        server.register_function(self.reply)

        # Clients don't have to listen to buy requests
        if self.role != BUYER:
            server.register_function(self.buy)
        
        server.serve_forever()


    def _print(self, msg, arg):
        with PRINT_LOCK:
            print(msg % arg)


    def _report_latency(self, t_start, t_stop):
        self.latency += (t_stop - t_start).total_seconds()
        self.request_count += 1
        if self.request_count % 50 == 0:
            self._print('**** [PERFORMANCE] Average latency of peer %d: %f (sec/req) ****',
                (self.peer_id, (self.latency / self.request_count)))


    def _get_proxy(self, peer_id):
        addr = PROXY_ADDR_LIST[peer_id] % (PORT_START_NUM + peer_id)
        proxy = xmlrpc.client.ServerProxy(addr)

        try:
            proxy.hello()       # ack
        except xmlrpc.client.Fault as err:
            self._print('[Proxy Error] code: %d, msg: %s', (err.faultCode, err.faultString))
            pass
        except xmlrpc.client.ProtocolError as err:
            self._print('[Proxy Error] code: %d, msg: %s', (err.errcode, err.errmsg))
            return None
        except socket.error:
            self._print('[Protocol Error] Failed to connect to peer %d', peer_id)
            return None
            
        return proxy


    # for thread to execute
    def _lookup_t(self, peer_id, product_name, hopcount, path):
        proxy = self._get_proxy(peer_id)
        if proxy != None:
            t_start = datetime.datetime.now()
            proxy.lookup(product_name, hopcount, path)
            t_stop = datetime.datetime.now()
            self._report_latency(t_start, t_stop)


    # for thread to execute
    def _reply_t(self, peer_id, seller_id, product_name, new_path):
        proxy = self._get_proxy(peer_id)
        if proxy != None:
            t_start = datetime.datetime.now()
            proxy.reply(seller_id, product_name, new_path)
            t_stop = datetime.datetime.now()
            self._report_latency(t_start, t_stop)
  

    def hello(self):
        return True


    def lookup(self, product_name, hopcount, path):
        footprints = path.split('-')
        
        # have the product
        if self.role != BUYER and product_name == self.commodity:
            from_neighbor_id = int(footprints[0])
            new_path = '' if len(footprints) == 1 else "-".join(footprints[1:])

            proxy = self._get_proxy(from_neighbor_id)
            if proxy != None:
                self._print("Peer %d has %s!! Reply to peer %d",
                    (self.peer_id, TO_ITEM_NAME[product_name], from_neighbor_id))

                thread = thd.Thread(target=self._reply_t,
                    args=(from_neighbor_id, self.peer_id, product_name, new_path))
                thread.start()

            return True

        # discard
        if hopcount == 0:
            self._print("[LOOKUP stop] Peer %d final path: %s", (self.peer_id, path))
            return False

        # propagate the request
        for neighbor_id in self.neighbors:
            if str(neighbor_id) not in footprints:
                new_path = "%d-%s" % (self.peer_id, path)
                
                self._print("[LOOKUP propagate] Peer %d: (next) %d <- %d (curr) - %s (path)",
                    (self.peer_id, neighbor_id, self.peer_id, path))

                thread = thd.Thread(target=self._lookup_t,
                    args=(neighbor_id, product_name, hopcount-1, new_path))
                thread.start()

        return True


    def reply(self, seller_id, product_name, path):
        # 1. The reply request arrives to the buyer
        if len(path) == 0:
            # target product has been updated (timeout)
            if product_name != self.target:
                return False

            t_response = datetime.datetime.now()
            self.response_time += (t_response - self.t_buy).total_seconds()
            self.candidate_sellers.append(seller_id)
            self._print("[RECEIVE] Peer %d receives a reply from peer %d", (self.peer_id, seller_id))
            
            return True
        
        # 2. Otherwise, a peer propagates the reply request
        footprints = path.split('-')
        next_neighbor_id = int(footprints[0])
        new_path = '' if len(footprints) == 1 else "-".join(footprints[1:])

        self._print("[REPLY propagate] Peer %d: (curr) %d -> %d (next) --> %s (path)",
            (self.peer_id, self.peer_id, next_neighbor_id, new_path))
        
        thread = thd.Thread(target=self._reply_t, args=(next_neighbor_id, seller_id, product_name, new_path))
        thread.start()

        return True


    def buy(self, product_name):
        if product_name != self.commodity:
            self._print("[FAILURE] The %s of peer %d has been sold out.",
                    (TO_ITEM_NAME[self.commodity], self.peer_id))
            return False

        # sync
        with self.commodity_lock:
            if self.commodity_quantity <= 0:
                self._print("[FAILURE] The %s of peer %d has been sold out.",
                    (TO_ITEM_NAME[self.commodity], self.peer_id))
                return False

            self.commodity_quantity -= 1
        
            if self.commodity_quantity == 0:
                self.commodity_quantity = random.randint(1, MAX_ITEM_NUMBER)
                self.commodity = random.randint(FISH, BOAR)
                if self.role == BOTH:
                    while self.commodity == self.target:
                        self.commodity = random.randint(FISH, BOAR)

        self._print("[UPDATE] Peer %d has %d units of %s to sell",
            (self.peer_id, self.commodity_quantity, TO_ITEM_NAME[self.commodity]))

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


def generate_peer_roles():
    buyer_num  = 0
    seller_num = 0
    roles = []

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
        
        roles.append(tmp)
    
    return roles
    

if __name__ == "__main__":
    if DEBUG:
        # only support self-defined neighbor map
        neighbor_map = TEST_MAP
        role = TEST_ROLE
        PEER_NUM = len(role)
    else:
        neighbor_map = generate_neighbor_map()
        role = generate_peer_roles()


    with PRINT_LOCK:
        print('Node is running on: %s\n' % CURR_IP)
        print('\\\\\\\\\\  *NEIGHBOR MAP*  /////')
        for row in neighbor_map:
            print(row)
        print('\n')


    peers = []
    # run at localhost
    if LOCAL_DEPLOY:
        for peer_id in range(PEER_NUM):
            neighbors = []
            for j in range(PEER_NUM):
                if neighbor_map[peer_id][j]:
                    neighbors.append(j)

            PROXY_ADDR_LIST.append('http://localhost:%d')
            peer = Peer(peer_id, role[peer_id], neighbors)
            peers.append(peer)
            peer.start()
    
    else:
        # find the order of current machine & create PROXY_ADDR_LIST
        # a machine with order 0 is the master machine
        curr_machine_order = 0
        num_of_peers_on_each_machine = int(PEER_NUM / len(MACHINES))
        for i in range(len(MACHINES)):
            if CURR_IP == MACHINES[i]['ip']:
                curr_machine_order = i
            
            peer_id_start = num_of_peers_on_each_machine * i
            peer_id_end   = peer_id_start + num_of_peers_on_each_machine
            for peer_id in range(peer_id_start, peer_id_end):
                PROXY_ADDR_LIST.append('http://' + MACHINES[i]['ip'] + ':%d')
        
        peer_id_start = num_of_peers_on_each_machine * curr_machine_order
        peer_id_end   = peer_id_start + num_of_peers_on_each_machine
        for peer_id in range(peer_id_start, peer_id_end):
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