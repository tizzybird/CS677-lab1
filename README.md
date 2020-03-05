# 677 Lab 1

This is the Git repo for 677 Lab 1. See http://lass.cs.umass.edu/~shenoy/courses/spring19/labs/lab1.html for a description of the lab. The lab is due on March 4, 23:55 hrs. Prior to submitting your project, replace this README file with the one that explains how to setup and run your code. Be sure to provide enough details fo us to run it in order to grade it.

---

### Setup

The "src/" folder contains below files:
- node.py
- define.py

This program can be executed on a single machine or two machines. Before executing this program, please properly adjust the settings in define.py.

To run the program on a single machine, please adjust define.py as below:
``` python
SCENARIO = 1
# adjustable
PORT_START_NUM = 10070
# adjustable
ADDR = "http://localhost:%d/"
```

To run the program on two machines, please define a master machine and a slave machine using their IP. Also, please specify peer IDs of each machine. Duplicated peer IDs are not allowed. Below is the default settings of define.py:
``` python
SCENARIO = 2
# default is elnux2, adjustable
MASTER_IP = "128.119.243.164"
# default is elnux2, adjustable
MASTER_ADDR = "http://128.119.243.164:%d"
# default is elnux7, adjustable
SLAVE_ADDR  = "http://128.119.243.175:%d"

# default is [0, 1] on master and [2, 3] on slave (4 peers). [0, 1, 3] / [2, 4, 5] (6 peers) are acceptable, but [0, 1, 2] / [0, 1, 2] are not
MASTER_PEER_ID = [0, 1]
SLAVE_PEER_ID  = [2, 3]
```

The neighbors and roles of peers are defined in define.py. Please redefine them if you want to change their connections or roles. Also note that if you want to add more peers, you need to define a larger list of test_map and test_role.
``` python
# Role of each peer. ex. peer_id=0 is a buyer, peer_id=3 is a buyer and a seller 
test_role = [BUYER, SELLER, SELLER, BOTH]
# The relationship between peers. ex. peer 0 and peer 1 are neighbors since test_map[0][1]=True. Note that test_map[1][0] should be set True at the same time.
test_map = [
    [False, True, False, True],
    [True, False, True, True],
    [False, True, False, True],
    [True, True, True, False]
]
```

There are several optional settings:
``` python
# the maximum number of items a seller can sell
MAX_ITEM_NUMBER = 10
# how long can a client wait for reply
CLIENT_TIMEOUT = 3
# hop counts
HOPCOUNT = 3
```


---
### Run
To run the program, simply type in below commands in a terminal:
``` sh
$> python3 node.py
```

To run the program on two machines, please type the above command in the terminal of master machine and the terminal of slave machine.