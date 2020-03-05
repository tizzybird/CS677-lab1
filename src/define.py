# DEBUG = True

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

# freezed
PEER_NUM = 6
MAX_BUYER_NUM  = int(PEER_NUM/2) + 1
MAX_SELLER_NUM = int(PEER_NUM/2) + 1

######## CONGIGURE THIS PART !!!!!!!!!! ########
# 1 for using only a machine
# 2 for using 2 machines
# other values are not supported
SCENARIO = 2
PORT_START_NUM = 10070

# >>>>> For one_machine_scenario()
ADDR = "http://localhost:%d/"


# >>>>> For two_machine_scenario
MASTER_IP = "128.119.243.164" # elnux2
MASTER_ADDR = "http://128.119.243.164:%d" # elnux2
SLAVE_ADDR  = "http://128.119.243.175:%d" # elnux7
MASTER_PEER_ID = [0, 1]
SLAVE_PEER_ID  = [2, 3]


# >>>>> optional
MAX_ITEM_NUMBER = 10
CLIENT_TIMEOUT = 3
HOPCOUNT = 3

######## SELF-DEFINED MAP & ROLE ########
# test_role = [BUYER, SELLER, SELLER]
# test_map = [
#     [False, True, False],
#     [True, False, True],
#     [False, True, False]
# ]

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
