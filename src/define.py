BUYER  = 1
SELLER = 2
BOTH   = 3

FISH = 11
SALT = 12
BOAR = 13
TO_ITEM_NAME = {
    FISH: 'Fish',
    SALT: 'Salt',
    BOAR: 'Boar'
}

############ CONGIGURABLE ############
# set True if you want to deploy locally
# setting True omits NUM_OF_PEER_ON_EACH_MACHINE and MACHINES
LOCAL_DEPLOY = True

# number of peers to be initialized on a machine
# Note that the number of peers on each machine = PEER_NUM / '# of MACHINES'
MACHINES = [{
    # default: elnux2
    'ip': '128.119.243.164'
}, {
    # defualt: elnux7
    'ip': '128.119.243.175'
}]

# number of total peers
# PEER_NUM would be updated to len(TEST_ROLE) if DEBUG is True
PEER_NUM = 6
MAX_BUYER_NUM  = int(PEER_NUM/2) + 1
MAX_SELLER_NUM = int(PEER_NUM/2) + 1

# optional
# default port to start a RPC server
# the port number of each RPC peer server is (PORT_START_NUM + peer_id)
PORT_START_NUM = 10070
# the maximum quantity a seller can sell
MAX_ITEM_NUMBER = 10
# waiting time for a buyer to receive responses from sellers
CLIENT_TIMEOUT = 4
# hopcount
HOPCOUNT = 3

######## SELF-DEFINED MAP & ROLE ########
# if you would like to initialize peers by using TEST_ROLE and TEST_MAP,
# please set DEBUG to True
DEBUG = True

# case 1
# TEST_ROLE = [BUYER, SELLER, BOTH]
# TEST_MAP  = [
#     [False, True, False],
#     [True, False, True],
#     [False, True, False]
# ]

# case 2
# TEST_ROLE = [BUYER, SELLER, SELLER, BOTH]
# TEST_MAP  = [
#     [False, True, False, True],
#     [True, False, True, True],
#     [False, True, False, True],
#     [True, True, True, False]
# ]

# case 3
# TEST_ROLE = [BUYER, BOTH, SELLER, BOTH]
# TEST_MAP  = [
#     [False, True, False, True],
#     [True, False, True, True],
#     [False, True, False, True],
#     [True, True, True, False]
# ]

# case 4 fully connected
TEST_ROLE = [BOTH, BOTH, BOTH, BOTH]
TEST_MAP  = [
    [False, True, True, True],
    [True, False, True, True],
    [True, True, False, True],
    [True, True, True, False]
]

# case 5
# TEST_ROLE = [BUYER, BOTH, SELLER, SELLER, BOTH, BUYER]
# TEST_MAP  = [
#     [False, True, False, True, True, False],
#     [True, False, True, False, True, True],
#     [False, True, False, True, False, False],
#     [True, False, True, False, False, False],
#     [True, True, False, False, False, True],
#     [False, True, False, False, True, False]
# ]

# case 6
# TEST_ROLE = [BUYER, SELLER, BOTH, BOTH, BOTH, BOTH]
# TEST_MAP  = [
#     [False, True, False, True, True, False],
#     [True, False, True, False, True, True],
#     [False, True, False, True, False, False],
#     [True, False, True, False, False, False],
#     [True, True, False, False, False, True],
#     [False, True, False, False, True, False]
# ]

# case 7 fully connected
# TEST_ROLE = [BOTH, BOTH, BOTH, BOTH, BOTH, BOTH]
# TEST_MAP  = [
#     [False, True, True, True, True, True],
#     [True, False, True, True, True, True],
#     [True, True, False, True, True, True],
#     [True, True, True, False, True, True],
#     [True, True, True, True, False, True],
#     [True, True, True, True, True, False]
# ]