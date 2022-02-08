from ftsa.protocols.utils.TimeMeasure import Clock
from ftsa.protocols.utils.CommMeasure import Bandwidth, User
from ftsa.protocols.ccsftsa17.client import Client
from ftsa.protocols.ccsftsa17.server import Server

import benchmark_utils

from math import ceil
from copy import deepcopy
import sys

DH_keysize = 256

def init_ccs17_scenario(scenario):
    
    Client.set_scenario(scenario.dimension, scenario.inputsize, DH_keysize,
     scenario.threshold, scenario.nclients)
    
    Server.set_scenario(scenario.dimension, scenario.inputsize, DH_keysize,
     scenario.threshold, scenario.nclients)

    clients = {}
    for i in range(scenario.nclients):
        idx = i+1
        clients[idx] = Client(idx)

    server = Server()

    return clients, server


def benchmark_ccs17(clients, server, scenario, repititions):

    online_round0_client_clock = Clock("online", "round0", "client", scenario)
    online_round0_server_clock = Clock("online", "round0", "server", scenario)
    online_round1_client_clock = Clock("online", "roudn1", "client", scenario)
    online_round1_server_clock = Clock("online", "round1", "server", scenario)
    online_round2_client_clock = Clock("online", "round2", "client", scenario)
    online_round2_server_clock = Clock("online", "round2", "server", scenario)
    online_round4_client_clock = Clock("online", "round4", "client", scenario)
    online_round4_server_clock = Clock("online", "round4", "server", scenario)

    online_round0_bandwith = Bandwidth("online", "round0", scenario)
    online_round1_bandwith = Bandwidth("online", "round1", scenario)
    online_round2_bandwith = Bandwidth("online", "round2", scenario)
    online_round4_bandwith = Bandwidth("online", "round4", scenario)

    ### **Round0** phase
    # The clients 
    allpks = {}
    allpkc = {}
    for i in range(scenario.nclients):
        clients[i+1].new_fl_step()
        online_round0_bandwith.measure_rcvd_data()
        online_round0_client_clock.measure_from_here()
        user, pks, pkc = clients[i+1].advertise_keys()
        online_round0_client_clock.measure_till_here()
        online_round0_bandwith.measure_sent_data((user, pks, pkc), User.size)
        allpks[user] = pks
        allpkc[user] = pkc

    # The server
    for i in range(repititions-1):
        server_copy = deepcopy(server)
        online_round0_server_clock.measure_from_here()
        _, _ = server_copy.advertise_keys(allpks, allpkc)
        online_round0_server_clock.measure_till_here()

    online_round0_server_clock.measure_from_here()
    allpks, allpkc = server.advertise_keys(allpks, allpkc)
    online_round0_server_clock.measure_till_here()



    ### **Round1** phase
    # The clients
    allekshares = {}
    for i in range(scenario.nclients):
        online_round1_bandwith.measure_rcvd_data((allpks, allpkc), User.size)
        online_round1_client_clock.measure_from_here()
        user, eshares = clients[i+1].share_keys(allpks, allpkc)
        online_round1_client_clock.measure_till_here()
        online_round1_bandwith.measure_sent_data((user, eshares), User.size)
        allekshares[user] = eshares

    # The server 
    for i in range(repititions-1):
        server_copy = deepcopy(server)
        online_round1_server_clock.measure_from_here()
        _ = server_copy.share_keys(allekshares)
        online_round1_server_clock.measure_till_here()

    online_round1_server_clock.measure_from_here()
    allekshares = server.share_keys(allekshares)
    online_round1_server_clock.measure_till_here()


    ### **Round2** phase
    # The clients
    allY = {}
    for i in range(scenario.nclients):
        online_round2_bandwith.measure_rcvd_data(allekshares[i+1], User.size)
        online_round2_client_clock.measure_from_here()
        user, Y = clients[i+1].masked_input_collection(allekshares[i+1])
        online_round2_client_clock.measure_till_here()
        online_round2_bandwith.measure_sent_data((user, Y), [User.size, Client.expandedvaluesize])
        allY[user] = Y

    # drop some clients
    nclientsnew = scenario.nclients - ceil(scenario.dropout * scenario.nclients)
    allY = {idx:y for idx, y in allY.items() if idx <= nclientsnew }
    
    # The server
    for i in range(repititions-1):
        server_copy = deepcopy(server)
        online_round2_server_clock.measure_from_here()
        _ = server_copy.masked_input_collection(allY)
        online_round2_server_clock.measure_till_here()

    online_round2_server_clock.measure_from_here()
    U3 = server.masked_input_collection(allY)
    online_round2_server_clock.measure_till_here()



    ### **Round4** phase
    # The clients
    allbshares = {}
    allkshares = {}
    for i in range(nclientsnew):
        online_round4_bandwith.measure_rcvd_data(U3, User.size)
        online_round4_client_clock.measure_from_here()
        user, kshares, bshares = clients[i+1].unmasking(U3)
        online_round4_client_clock.measure_till_here()
        online_round4_bandwith.measure_sent_data((user, kshares, bshares), User.size)
        allbshares[user] = bshares 
        allkshares[user] = kshares

    for i in range(repititions-1):
        server_copy = deepcopy(server)
        online_round4_server_clock.measure_from_here()
        _ = server_copy.unmasking(allkshares, allbshares)
        online_round4_server_clock.measure_till_here()

    online_round4_server_clock.measure_from_here()
    sumX = server.unmasking(allkshares, allbshares)
    online_round4_server_clock.measure_till_here()


    # Verify the results
    summ=clients[1].X
    from operator import add
    for i in range(1, nclientsnew):
        summ = list(map(add, summ, clients[i+1].X))


    online_round0_client_clock.finish()
    online_round0_server_clock.finish()
    online_round1_client_clock.finish()
    online_round1_server_clock.finish()
    online_round2_client_clock.finish()
    online_round2_server_clock.finish()
    online_round4_client_clock.finish()
    online_round4_server_clock.finish()

    online_round0_bandwith.finish()
    online_round1_bandwith.finish()
    online_round2_bandwith.finish()
    online_round4_bandwith.finish()

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
        print("Usage: benchmarks_ccs17.py <time_benchmarks.csv> <comm_benchmarks.csv> [comma seprated run numbers (no spaces)]")
        print("\t use [-p] to only see the existing runs")
        sys.exit(-1)

    benchmark_utils.keysize = DH_keysize
    benchmark_utils.benchmark(benchmark_ccs17, init_ccs17_scenario, dont_run, runs)