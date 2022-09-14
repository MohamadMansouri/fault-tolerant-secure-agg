from ftsa.protocols.buildingblocks.JoyeLibert import TJLS
from ftsa.protocols.utils.TimeMeasure import Clock
from ftsa.protocols.utils.CommMeasure import Bandwidth, User
from ftsa.protocols.ourftsa22.client import Client
from ftsa.protocols.ourftsa22.server import Server

import benchmark_utils

from math import ceil
from copy import deepcopy
import sys

TJL_keysize = 2048

def init_ours_scenario(scenario):
    
    publicparam, _ , _ = TJLS(scenario.nclients, scenario.threshold).Setup(TJL_keysize)

    Client.set_scenario(scenario.dimension, scenario.inputsize, TJL_keysize,
     scenario.threshold, scenario.nclients, publicparam)
    
    Server.set_scenario(scenario.dimension, scenario.inputsize, TJL_keysize,
     scenario.threshold, scenario.nclients, publicparam)

    clients = {}
    for i in range(scenario.nclients):
        idx = i+1
        clients[idx] = Client(idx)

    server = Server()

    return clients, server
    
def benchmark_ours(clients, server, scenario, repititions):

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
    nclientsnew = scenario.nclients - ceil(scenario.dropout * scenario.nclients)
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
    Yzeroshares = {}
    for i in range(nclientsnew):
        online_construct_bandwith.measure_rcvd_data(allebshares[i+1], User.size)
        online_construct_client_clock.measure_from_here()
        user, bshares, Yzeroshare = clients[i+1].online_construct(allebshares[i+1])
        online_construct_client_clock.measure_till_here()
        online_construct_bandwith.measure_sent_data((user, bshares, Yzeroshare), User.size)
        allbshares[user] = bshares 
        Yzeroshares[user] = Yzeroshare

    # The server
    for i in range(repititions-1):
        server_copy = deepcopy(server)
        online_construct_server_clock.measure_from_here()
        _ = server_copy.online_construct(allbshares, Yzeroshares.values())
        online_construct_server_clock.measure_till_here()

    online_construct_server_clock.measure_from_here()
    sumX = server.online_construct(allbshares, Yzeroshares.values())
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
    runs = []
    dont_run = False
    try:

        if [x for x in sys.argv if x == '-p']: dont_run = True; print("Just printing run details")
        else:
            if len(sys.argv) >= 3:
                Clock.LOGFILE = sys.argv[1]
                Bandwidth.LOGFILE = sys.argv[2]
            else:
                raise()
                
            if len(sys.argv) == 4:
                runs = [int(x) for x in sys.argv[3].split(",")]
            if len(sys.argv) > 4:
                raise()
    except:
        print("Usage: benchmarks_ours.py <time_benchmarks.csv> <comm_benchmarks.csv> [comma separated run numbers (no spaces)]")
        print("\t use [-p] to only see the existing runs")
        sys.exit(-1)

    benchmark_utils.keysize = TJL_keysize
    benchmark_utils.benchmark(benchmark_ours, init_ours_scenario,dont_run, runs)