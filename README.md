# 677 Lab 1

This is the Git repo for 677 Lab 1. See http://lass.cs.umass.edu/~shenoy/courses/spring19/labs/lab1.html for a description of the lab. The lab is due on March 4, 23:55 hrs. Prior to submitting your project, replace this README file with the one that explains how to setup and run your code. Be sure to provide enough details fo us to run it in order to grade it.

---

### Setup

The "src/" folder contains below files:
- node.py
- define.py

This program can be executed on localhost or on multiple machines. Before executing this program, please properly adjust corresponding settings in define.py.

To run the program on localhost, please adjust define.py as below:
``` python
# set True if you want to deploy locally
# setting True omits NUM_OF_PEER_ON_EACH_MACHINE and MACHINES
LOCAL_DEPLOY = True
# number of total peers
# PEER_NUM would be updated to len(TEST_ROLE) if DEBUG is True
PEER_NUM = 6
```

To run the program multiple machines, please specify the IP address of each machine in MACHINES. The program will assign peer ID based on the order of machine and total PEER_NUM. For example, if PEER_NUM=6 and MACHINES=[{'ip': '128.119.243.164'}, {'ip': '128.119.243.175'}], then peer IDs (0, 1, 2) are assigned to machine '128.119.243.164' and peer IDs (3, 4, 5) are assigned to machine '128.119.243.175' automatically. Below is the default settings of define.py for running on multiple machines:
``` python
# set True if you want to deploy locally
# setting True omits NUM_OF_PEER_ON_EACH_MACHINE and MACHINES
LOCAL_DEPLOY = False
# number of total peers
# PEER_NUM would be updated to len(TEST_ROLE) if DEBUG is True
PEER_NUM = 6
# number of peers to be initialized on a machine
# Note that the number of peers on each machine = PEER_NUM / '# of MACHINES'
MACHINES = [{
    # default: elnux2
    'ip': '128.119.243.164'
}, {
    # defualt: elnux7
    'ip': '128.119.243.175'
}]
```

The neighbors and roles of peers are defined in define.py. Please redefine them if you want to change their relations or roles. Also note that if you want to add more peers, you need to define a larger list of TEST_MAP and TEST_ROLE.
``` python
# Role of each peer. ex. peer_id=0 is a buyer, peer_id=3 is a buyer and a seller 
TEST_ROLE = [BUYER, BOTH, SELLER, SELLER, BOTH, BUYER]
# The relationship between peers. ex. peer 0 and peer 1 are neighbors since test_map[0][1]=True. Note that test_map[1][0] should be set True at the same time.
TEST_MAP  = [
    [False, True, False, True, True, False],
    [True, False, True, False, True, True],
    [False, True, False, True, False, False],
    [True, False, True, False, False, False],
    [True, True, False, False, False, True],
    [False, True, False, False, True, False]
]

```

There are several optional settings:
``` python
# default port to start a RPC server
# the port number of each RPC peer server is (PORT_START_NUM + peer_id)
PORT_START_NUM = 10070
# the maximum quantity a seller can sell
MAX_ITEM_NUMBER = 10
# waiting time for a buyer to receive responses from sellers
CLIENT_TIMEOUT = 4
# hopcount
HOPCOUNT = 3
```


---
### Run
This program has been tested with python 3.5.2. and 3.7.3. To run the program, simply type in below command in the terminal of a machine after properly configuring define.py. If you would like to run the program on multiple machines, please type in below command in the terminal of each machine:
``` sh
$> python3 node.py
```