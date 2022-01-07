from protocols.ourftsa22.client import Client
from protocols.ourftsa22.server import Server
from protocols.buildingblocks.JoyeLibert import JLS
from protocols.utils.Scenario import Scenario
from protocols.utils.TimeMeasure import Clock
from protocols.utils.CommMeasure import Bandwidth, User

from math import ceil
from copy import deepcopy
import sys

REPITIONS = 10
DIMLIST = [1000, 2000, 4000, 6000, 8000, 10000, 20000, 40000, 60000, 80000, 100000, 200000, 300000, 400000, 500000]
INPUTSIZE = 16 
KEYSIZE = 2048
NCNTLIST = [100, 200, 300, 400, 500, 1000]
THRESHOLD = 2/3
DROPLIST = [0.0, 0.1, 0.2, 0.3]

def init_scenario(scenario):
    publicparam, _ , _ = JLS(nclients, inputsize, dimension).generate_keys()
    
    Client.set_scenario(scenario.dimension, scenario.inputsize,scenario.keysize,
     scenario.threshold, scenario.nclients, publicparam)
    
    Server.set_scenario(scenario.dimension, scenario.inputsize,scenario.keysize,
     scenario.threshold, scenario.nclients, publicparam)

    clients = {}
    for i in range(nclients):
        idx = i+1
        clients[idx] = Client(idx)

    server = Server()

    return clients, server



def run_benchmark(clients, server, scenario, repititions):

    setup_register_client_clock = Clock("setup", "register", "client", scenario)
    setup_register_server_clock = Clock("setup", "register", "server", scenario)
    setup_keysetup1_client_clock = Clock("setup", "keysetup1", "client", scenario)
    setup_keysetup2_client_clock = Clock("setup", "keysetup2", "client", scenario)
    setup_keysetup_server_clock = Clock("setup", "keysetup", "server", scenario)
    online_encrypt_client_clock = Clock("online", "encrypt", "client", scenario)
    online_encrypt_server_clock = Clock("online", "encrypt", "server", scenario)
    online_construct_client_clock = Clock("online", "construct", "client", scenario)
    online_construct_server_clock = Clock("online", "construct", "server", scenario)

    setup_register_bandwith = Bandwidth("setup", "register", scenario)
    setup_keysetup1_bandwith = Bandwidth("setup", "keysetup1", scenario)
    setup_keysetup2_bandwith = Bandwidth("setup", "keysetup2", scenario)
    online_encrypt_bandwith = Bandwidth("online", "encrypt", scenario)
    online_construct_bandwith = Bandwidth("online", "construct", scenario)

    ### **Setup-Register** phase
    # The clients 
    allpks = {}
    allpkc = {}
    for i in range(scenario.nclients):
        setup_register_bandwith.measure_rcvd_data()
        setup_register_client_clock.measure_from_here()
        user, pks, pkc = clients[i+1].setup_register()
        setup_register_client_clock.measure_till_here()
        setup_register_bandwith.measure_sent_data((user, pks, pkc), User.size)
        allpks[user] = pks
        allpkc[user] = pkc

    # The server
    for i in range(repititions-1):
        server_copy = deepcopy(server)
        setup_register_server_clock.measure_from_here()
        _, _ = server_copy.setup_register(allpks, allpkc)
        setup_register_server_clock.measure_till_here()

    setup_register_server_clock.measure_from_here()
    allpks, allpkc = server.setup_register(allpks, allpkc)
    setup_register_server_clock.measure_till_here()



    ### **Setup-KeySetup** phase
    # The clients
    allekshares = {}
    for i in range(scenario.nclients):
        setup_keysetup1_bandwith.measure_rcvd_data((allpks, allpkc), User.size)
        setup_keysetup1_client_clock.measure_from_here()
        user, eshares = clients[i+1].setup_keysetup(allpks, allpkc)
        setup_keysetup1_client_clock.measure_till_here()
        setup_keysetup1_bandwith.measure_sent_data((user, eshares), User.size)
        allekshares[user] = eshares

    # The server 
    for i in range(repititions-1):
        server_copy = deepcopy(server)
        setup_keysetup_server_clock.measure_from_here()
        _ = server_copy.setup_keysetup(allekshares)
        setup_keysetup_server_clock.measure_till_here()

    setup_keysetup_server_clock.measure_from_here()
    allekshares = server.setup_keysetup(allekshares)
    setup_keysetup_server_clock.measure_till_here()

    # The clients
    for i in range(scenario.nclients):
        setup_keysetup2_bandwith.measure_rcvd_data(allekshares[i+1], User.size)
        setup_keysetup2_client_clock.measure_from_here()
        clients[i+1].setup_keysetup2(allekshares[i+1])
        setup_keysetup2_client_clock.measure_till_here()
        setup_keysetup2_bandwith.measure_sent_data()


    ### **Online-Encrypt** phase
    # The clients
    allebshares = {}
    allY = {}
    for i in range(scenario.nclients):
        clients[i+1].new_fl_step()
        online_encrypt_bandwith.measure_rcvd_data()
        online_encrypt_client_clock.measure_from_here()
        user, eshares, Y = clients[i+1].online_encrypt()
        online_encrypt_client_clock.measure_till_here()
        online_encrypt_bandwith.measure_sent_data((user, eshares, Y), User.size)
        allebshares[user] = eshares
        allY[user] = Y

    # drop some clients
    nclientsnew = scenario.nclients - ceil(scenario.dropout * nclients)
    allY = {idx:y for idx, y in allY.items() if idx <= nclientsnew }
    allebshares = {idx:y for idx, y in allebshares.items() if idx <= nclientsnew }

    # The server
    for i in range(repititions-1):
        server_copy = deepcopy(server)
        online_encrypt_server_clock.measure_from_here()
        _ = server_copy.online_encrypt(allebshares, allY)
        online_encrypt_server_clock.measure_till_here()

    online_encrypt_server_clock.measure_from_here()
    allebshares = server.online_encrypt(allebshares, allY)
    online_encrypt_server_clock.measure_till_here()



    ### **Online-Construct** phase
    # The clients
    allbshares = {}
    Ybarshares = {}
    for i in range(nclientsnew):
        online_construct_bandwith.measure_rcvd_data(allebshares[i+1], User.size)
        online_construct_client_clock.measure_from_here()
        user, bshares, Ybarshare = clients[i+1].online_construct(allebshares[i+1])
        online_construct_client_clock.measure_till_here()
        online_construct_bandwith.measure_sent_data((user, bshares, Ybarshare), User.size)
        allbshares[user] = bshares 
        Ybarshares[user] = Ybarshare

    # The server
    YbarsharesValues = list(Ybarshares.values())
    if YbarsharesValues.count(None) == len(YbarsharesValues):
        Ybarshares = None

    for i in range(repititions-1):
        server_copy = deepcopy(server)
        online_construct_server_clock.measure_from_here()
        _ = server_copy.online_construct(allbshares, Ybarshares)
        online_construct_server_clock.measure_till_here()

    online_construct_server_clock.measure_from_here()
    sumX = server.online_construct(allbshares, Ybarshares)
    online_construct_server_clock.measure_till_here()


    # Verify the results
    summ=clients[1].X
    from operator import add
    for i in range(1, nclientsnew):
        summ = list(map(add, summ, clients[i+1].X))


    setup_register_client_clock.finish()
    setup_register_server_clock.finish()
    setup_keysetup1_client_clock.finish()
    setup_keysetup2_client_clock.finish()
    setup_keysetup_server_clock.finish()
    online_encrypt_client_clock.finish()
    online_encrypt_server_clock.finish()
    online_construct_client_clock.finish()
    online_construct_server_clock.finish()

    setup_register_bandwith.finish()
    setup_keysetup1_bandwith.finish()
    setup_keysetup2_bandwith.finish()
    online_encrypt_bandwith.finish()
    online_construct_bandwith.finish()

    return sumX == summ



if __name__ == "__main__":

    if len(sys.argv) == 3:
        Clock.LOGFILE = sys.argv[1]
        Bandwidth.LOGFILE = sys.argv[2]
    else:
        if len(sys.argv) != 1:
            print("Usage: benchmarks.py [time_benchmarks.csv] [comm_benchmarks.csv]")
            sys.exit(-1)
    
    Bandwidth.LOGFILE = "ours_" + Bandwidth.LOGFILE
    
    dimensions = DIMLIST
    inputsize = INPUTSIZE 
    keysize = KEYSIZE
    nclientss = NCNTLIST
    threshold = THRESHOLD
    dropouts = DROPLIST

    total = len(dimensions) * len(nclientss) * len(dropouts)
    success = {False : 0, True : 0}
    counter = 0 

    for dimension in dimensions:
        for nclients in nclientss:
            for dropout in dropouts:

                counter += 1
                print("Test number {}/{} ({}/{} succesfull): dimension = {}, nclients = {}, dropout = {}".format(
                    counter, total, success[True], success[True] + success[False], dimension, nclients, dropout))

                scenario = Scenario(dimension, inputsize, keysize, ceil(threshold*nclients), nclients, dropout)
                clients, server = init_scenario(scenario)
                valid = run_benchmark(clients, server, scenario, REPITIONS, )
                success[valid] += 1
    

    print("Finished. Succesfull tests: {}/{}".format(success[True], success[True] + success[False]))

