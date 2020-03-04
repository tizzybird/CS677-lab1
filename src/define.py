DEBUG = True

BUYER  = 1
SELLER = 2
BOTH   = 3

FISH = 11
SALT = 12
BOAR = 13
TO_ITEM_NAME = {
    FISH: 'fish',
    SALT: 'salt',
    BOAR: 'boar'
}

MAX_ITEM_NUMBER = 10
CLIENT_TIMEOUT = 5


# For one_machine_scenario()
PEER_NUM = 6
MAX_BUYER_NUM  = int(PEER_NUM/2) + 1
MAX_SELLER_NUM = int(PEER_NUM/2) + 1
ADDR = "http://localhost:%d/"
PORT_START_NUM = 10070

# test_role = [BUYER, SELLER, SELLER]
# test_map = [
#     [False, True, False],
#     [True, False, True],
#     [False, True, False]
# ]

######## CONGIGURE THIS PART !!!!!!!!!! ########
# For two_machine_scenario
MASTER_IP = "128.119.243.164"
MASTER_ADDR = "http://128.119.243.164:%d"
SLAVE_ADDR  = "http://128.119.243.175:%d"
MASTER_PEER_ID = [0, 1]
SLAVE_PEER_ID  = [2, 3]

test_role = [BUYER, SELLER, SELLER, BOTH]
test_map = [
    [False, True, False, True],
    [True, False, True, True],
    [False, True, False, True],
    [True, True, True, False]
]

# test_role = [BUYER, BOTH, SELLER, SELLER, BOTH, BUYER]
# test_map = [
#     [False, True, False, True, True, False],
#     [True, False, True, False, True, True],
#     [False, True, False, True, False, False],
#     [True, False, True, False, False, False],
#     [True, True, False, False, False, True],
#     [False, True, False, False, True, False]
# ]
