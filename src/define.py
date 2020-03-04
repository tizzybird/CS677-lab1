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

ADDR = "http://localhost:%d/"
PORT_START_NUM = 10070

CLIENT_TIMEOUT = 5

PEER_NUM = 6
MAX_BUYER_NUM  = int(PEER_NUM/2) + 1
MAX_SELLER_NUM = int(PEER_NUM/2) + 1

# test_role = [BUYER, SELLER, SELLER]
# test_map = [
#     [False, True, False],
#     [True, False, True],
#     [False, True, False]
# ]

test_role = [BUYER, SELLER, SELLER, BOTH]
test_map = [
    [False, True, False, True],
    [True, False, True, False],
    [False, True, False, True],
    [True, False, True, False]
]

test_role = [BUYER, BOTH, SELLER, SELLER, BOTH, BUYER]
test_map = [
    [False, True, False, True, True, False],
    [True, False, True, False, True, True],
    [False, True, False, True, False, False],
    [True, False, True, False, False, False],
    [True, True, False, False, False, True],
    [False, True, False, False, True, False]
]
