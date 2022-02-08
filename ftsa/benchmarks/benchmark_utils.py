from ftsa.protocols.utils.Scenario import Scenario

from math import ceil

REPS = 5
dimensions = [1000, 100000] # and 10000
inputsize = 16 
nclientss = [100, 300] # and 600
threshold = 2/3
dropouts = [0.0, 0.1, 0.3]
keysize = None
Client = None
Server = None


def benchmark(benchmark, init_scenario, dont_run=False, runs=[] ):

    total = len(dimensions) * len(dropouts) + len(nclientss) * len(dropouts)
    success = {False : 0, True : 0}
    counter = 0 

    dimension = 10000
    for nclients in nclientss:
        for dropout in dropouts:

            counter += 1
            if dont_run: 
                print("run {}: dimension = {}, nclients = {}, dropout = {}".format(counter, dimension, nclients, dropout))
                continue

            if runs and counter not in runs:
                continue
            
            print("Run number {}/{} ({}/{} succesfull): dimension = {}, nclients = {}, dropout = {}".format(
                counter, total, success[True], success[True] + success[False], dimension, nclients, dropout))

            

            scenario = Scenario(dimension, inputsize, keysize, ceil(threshold*nclients), nclients, dropout)
            clients, server = init_scenario(scenario)
            valid = benchmark(clients, server, scenario, REPS)
            success[valid] += 1

    nclients = 600    
    for dimension in dimensions:
        for dropout in dropouts:

            counter += 1
            if dont_run: 
                print("run {}: dimension = {}, nclients = {}, dropout = {}".format(counter, dimension, nclients, dropout))
                continue

            if runs and counter not in runs:
                continue
            
            print("Run number {}/{} ({}/{} succesfull): dimension = {}, nclients = {}, dropout = {}".format(
                counter, total, success[True], success[True] + success[False], dimension, nclients, dropout))
            
            
            scenario = Scenario(dimension, inputsize, keysize, ceil(threshold*nclients), nclients, dropout)
            clients, server = init_scenario(scenario)
            valid = benchmark(clients, server, scenario, REPS)    
            success[valid] += 1

    print("Finished. Successful tests: {}/{}".format(success[True], success[True] + success[False]))
