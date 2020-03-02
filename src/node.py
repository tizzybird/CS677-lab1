import xmlrpc
from xmlrpc.server import SimpleXMLRPCServer

import json
import socket
import threading as thd
from threading import Lock

import random
import time

BUYER  = 1
SELLER = 2
BOTH   = 3

PEER_NUM = 6

ADDR = socket.gethostbyname(socket.gethostname())
PORT_START_NUM = 10070

MAX_BUYER_NUM  = 2
MAX_SELLER_NUM = 2

print_lock = Lock()

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
        server = thd.Thread(target=self.start_peer_server)
        server.start()

        if self.role == BUYER or self.role == BOTH:
            for i in self.neighbors:
                addr = "http://localhost:%d/" % (PORT_START_NUM+i)
                proxy = xmlrpc.client.ServerProxy(addr)
                with print_lock:
                    print ("-------------> Peer %d calls neighbor %d" % (self.peer_id, i))
                
                # testing
                if proxy.show_me_some_message(self.peer_id):
                    with print_lock:
                        print ("-------------- Peer %d finishes calling" % (self.peer_id))
        
        server.join()

    
    # for testing
    def show_me_some_message(self, sMsg):
        with print_lock:
            print ("<------------- Peer %d receives a call from %s" % (self.peer_id, sMsg))

        return True


    def start_peer_server(self):
        with print_lock:
            print("The server of peer %d is running" % self.peer_id)
        server = SimpleXMLRPCServer(("localhost", PORT_START_NUM + self.peer_id))
        server.register_function(self.show_me_some_message)
        server.serve_forever()


    def lookup(self, product_name, hopcount):
        pass

    def reply(self, seller_id):
        pass

    def buy(self, seller_id):
        pass


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
