from copy import deepcopy
from os import listdir, read
from os.path import isdir, isfile, join
import csv
from collections import defaultdict
from matplotlib import colors
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.patches as mpatches

from numpy.core.fromnumeric import mean

from ftsa.protocols.utils.Scenario import Scenario



font = {'size'   : 13}
mpl.rc('font', **font)
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman'] + plt.rcParams['font.serif']

mpl.rcParams['axes.linewidth'] = 1.5 #set the value globally

ccs_data_dir = "./results/ccs17"
ours_data_dir = "./results/ours"

plots_dir = "./plots/"

scenarios = set()

def update_scenarios(s):
    if s not in scenarios:
        scenarios.add(s)



def parsetime(dir):
    data_client_setup = defaultdict(lambda: defaultdict(list))
    data_client_online = defaultdict(lambda: defaultdict(list))
    data_server_setup = defaultdict(lambda: defaultdict(list))
    data_server_online = defaultdict(lambda: defaultdict(list))
    files = []
    for f in listdir(dir):
        fullf = join(dir,f)
        if isdir(fullf) and fullf != 'uncompleted':
            for ff in listdir(fullf):
                if ff[:4] == "time":
                    files.append(join(fullf,ff))
                
        elif isfile(fullf):
            if f[:4] == "time":
                files.append(fullf)
    
    for file in files:
        with open(file) as f:
            reader = csv.reader(f)
            next(reader, None)  # skip the headers
            for row in reader:
                s = Scenario()
                s.fromstrlist(row[:s.len()])
                update_scenarios(s)
                entity = row[s.len()]
                phase = row[s.len()+1]
                round = row[s.len()+2]
                if round == "roudn1":
                    round = "round1"
                value = float(row[s.len()+3])
                if entity == "client":
                    if phase == "setup":
                        data_client_setup[s][round] += [value]
                    elif phase == "online":
                        data_client_online[s][round] += [value]
                    else:
                        raise ValueError("Unkown phase {}".format(phase))
                elif entity == "server":
                    if phase == "setup":
                        data_server_setup[s][round] += [value]
                    elif phase == "online":
                        data_server_online[s][round] += [value]
                else:
                    raise ValueError("Unkown entity {}".format(entity))
    return data_client_setup, data_client_online, data_server_setup, data_server_online

def parsecomm(dir):
    data_setup_sent = defaultdict(lambda: defaultdict(list))
    data_online_sent = defaultdict(lambda: defaultdict(list))
    data_setup_rcvd = defaultdict(lambda: defaultdict(list))
    data_online_rcvd = defaultdict(lambda: defaultdict(list))
    files = []
    for f in listdir(dir):
        fullf = join(dir,f)
        if isdir(fullf) and fullf != 'uncompleted':
            for ff in listdir(fullf):
                if ff[:4] == "comm":
                    files.append(join(fullf,ff))
        elif isfile(fullf):
            if f[:4] == "comm":
                files.append(fullf)
    
    for file in files:
        with open(file) as f:
            reader = csv.reader(f)
            next(reader, None)  # skip the headers
            for row in reader:
                s = Scenario()
                s.fromstrlist(row[:s.len()])
                update_scenarios(s)
                phase = row[s.len()]
                round = row[s.len()+1]
                direction = row[s.len()+2]
                value = int(row[s.len()+3])
                if direction == "sent":
                    if phase == "setup":
                        data_setup_sent[s][round] += [value]
                    elif phase == "online":
                        data_online_sent[s][round] += [value]
                    else:
                        raise ValueError("Unkown phase {}".format(phase))
                elif direction == "rcvd":
                    if phase == "setup":
                        data_setup_rcvd[s][round] += [value]
                    elif phase == "online":
                        data_online_rcvd[s][round] += [value]
                else:
                    raise ValueError("Unkown direction {}".format(direction))
    return data_setup_sent, data_setup_rcvd, data_online_sent, data_online_rcvd



def plot_time_client(ccs, online):
    
    drops = [0.0, 0.1]

    structdrops = {0.0:{}, 0.1:{}, 0.2:{}, 0.3:{}}
    structdata = {100000 : deepcopy(structdrops), 10000 : deepcopy(structdrops), 1000 : deepcopy(structdrops)}

    ccs_mean  = deepcopy(structdata)
    ccs_std = deepcopy(structdata)
    online_mean = deepcopy(structdata)
    online_std = deepcopy(structdata)

    for s in scenarios:
        if s.dimension not in structdata:
            continue

        ccs_mean[s.dimension][s.dropout][s.nclients] = np.mean(ccs[s]['round0']) + np.mean(ccs[s]['round1']) + np.mean(ccs[s]['round2']) + np.mean(ccs[s]['round4'])
        ccs_std[s.dimension][s.dropout][s.nclients] = np.std(ccs[s]['round0']) + np.std(ccs[s]['round1']) + np.std(ccs[s]['round2']) + np.std(ccs[s]['round4'])

        online_mean[s.dimension][s.dropout][s.nclients] = np.mean(online[s]['encrypt']) + np.mean(online[s]['construct'])
        online_std[s.dimension][s.dropout][s.nclients] = np.std(online[s]['encrypt']) + np.std(online[s]['construct'])


    nclients = [100, 300, 600]
    wdth = 0.4
    sep = wdth/8
    xsep = 1.5
    xes = ['ccs17', 'online']
    clrs = [['#99CCFF', '#99CCFF'], ['#f0938a', '#f0938a'],['#00CC99','#00CC99']]
    htch = ['x', None]



    fig, ax = plt.subplots()
    fig.set_figheight(4)
    fig.set_figwidth(8)
    # ax = axes[0]
    ax.set_ylabel('seconds')
    ax.set_xlabel('# clients')
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)

    x_ticks = []
    i = 0
    for ncli in nclients:
        x_pos = [xsep*i-wdth/2-sep, xsep*i+wdth/2+sep]
        x_ticks.append(xsep*i)
        j = len(drops)
        for drop in reversed(drops):
            j-=1
            means = np.array([ccs_mean[10000][drop][ncli], online_mean[10000][drop][ncli]])
            error = np.array([ccs_std[10000][drop][ncli], online_std[10000][drop][ncli]])
            ax.bar(x_pos, means, yerr=error, align='center', alpha=1, ecolor='black', color =clrs[j], hatch=htch,capsize=6, width=wdth)
            # print(ncli, drop, means[0]/means[1])


        i+=1


    ax.set_xticks(x_ticks)
    ax.set_xticklabels(nclients)


    handles = [
        mpatches.Patch(facecolor=clrs[0][0],hatch='xx', label='CCS17'), 
        mpatches.Patch(facecolor=clrs[0][0], label='No Failures'), 
        # mpatches.Patch(facecolor=clrs[1][0],hatch='xx', label='CCS17 (With Dropouts)'), 
        mpatches.Patch(facecolor=clrs[1][0], label='With Failures'), 
    ]

    lg = fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(.15, .85), borderaxespad=0)

    plt.savefig(plots_dir + 'time_client_clients.png', bbox_extra_artists=(lg,),bbox_inches='tight', dpi=400)


    fig, ax = plt.subplots()
    fig.set_figheight(4)
    fig.set_figwidth(8)
    dims = [1000, 10000, 100000]
    dimsnames = ['1K', '10K', '100K']
    ncli = 600 

    ax.set_ylabel('seconds')
    ax.set_xlabel('Dimension')
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)

    x_ticks = []
    i = 0
    for dim in dims:
        x_pos = [xsep*i-wdth/2-sep, xsep*i+wdth/2+sep]
        x_ticks.append(xsep*i)
        j = len(drops)
        for drop in reversed(drops):
            j-=1
            means = np.array([ccs_mean[dim][drop][ncli], online_mean[dim][drop][ncli]])
            error = np.array([ccs_std[dim][drop][ncli], online_std[dim][drop][ncli]])
            ax.bar(x_pos, means, yerr=error, align='center', alpha=1, ecolor='black', color =clrs[j], hatch=htch,capsize=6, width=wdth)
        i+=1


    ax.set_xticks(x_ticks)
    ax.set_xticklabels(dimsnames)


    handles = [
        mpatches.Patch(facecolor=clrs[0][0],hatch='xx', label='CCS17'), 
        mpatches.Patch(facecolor=clrs[0][0], label='No Failures'), 
        # mpatches.Patch(facecolor=clrs[1][0],hatch='xx', label='CCS17 (With Dropouts)'), 
        mpatches.Patch(facecolor=clrs[1][0], label='With Failures'), 
    ]

    lg = fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(.15, .85), borderaxespad=0)

    plt.savefig(plots_dir + 'time_client_dims.png', bbox_extra_artists=(lg,),bbox_inches='tight', dpi=400)

def plot_comm(ccs_sent, ccs_rcvd, online_sent, online_rcvd):
    
    drops = [0.0, 0.1]

    structdrops = {0.0:{}, 0.1:{}, 0.2:{}, 0.3:{}}
    structdata = {100000 : deepcopy(structdrops), 10000 : deepcopy(structdrops), 1000 : deepcopy(structdrops)}

    ccs_sent_mean  = deepcopy(structdata)
    ccs_rcvd_mean  = deepcopy(structdata)
    ccs_sent_std = deepcopy(structdata)
    ccs_rcvd_std = deepcopy(structdata)

    online_sent_mean = deepcopy(structdata)
    online_rcvd_mean = deepcopy(structdata)
    online_sent_std = deepcopy(structdata)
    online_rcvd_std = deepcopy(structdata)
    
    for s in scenarios:
        if s.dimension not in structdata:
            continue

        ccs_sent_mean[s.dimension][s.dropout][s.nclients] = np.mean(ccs_sent[s]['round0']) + np.mean(ccs_sent[s]['round1']) + np.mean(ccs_sent[s]['round2']) + np.mean(ccs_sent[s]['round4'])
        ccs_sent_std[s.dimension][s.dropout][s.nclients] = np.std(ccs_sent[s]['round0']) + np.std(ccs_sent[s]['round1']) + np.std(ccs_sent[s]['round2']) + np.std(ccs_sent[s]['round4'])
        ccs_rcvd_mean[s.dimension][s.dropout][s.nclients] = np.mean(ccs_rcvd[s]['round1']) + np.mean(ccs_rcvd[s]['round2']) + np.mean(ccs_rcvd[s]['round4'])
        ccs_rcvd_std[s.dimension][s.dropout][s.nclients] = np.std(ccs_rcvd[s]['round1']) + np.std(ccs_rcvd[s]['round2']) + np.std(ccs_rcvd[s]['round4'])

        online_sent_mean[s.dimension][s.dropout][s.nclients] = np.mean(online_sent[s]['encrypt']) + np.mean(online_sent[s]['construct'])
        online_sent_std[s.dimension][s.dropout][s.nclients] = np.std(online_sent[s]['encrypt']) + np.std(online_sent[s]['construct'])
        online_rcvd_mean[s.dimension][s.dropout][s.nclients] = np.mean(online_rcvd[s]['construct'])
        online_rcvd_std[s.dimension][s.dropout][s.nclients] = np.std(online_rcvd[s]['construct'])

    nclients = [100, 300, 600]
    wdth = 0.4
    sep = wdth/8
    xsep = 1.5
    xes = ['ccs17', 'online']
    clrs = [['#00CC99','#00CC99'], ['#f0938a', '#f0938a'],['#99CCFF', '#99CCFF']]
    htch = ['x', None]

    fig, ax = plt.subplots()
    fig.set_figheight(4)
    fig.set_figwidth(8)
    ax.set_ylabel('Data (MB)')
    ax.set_xlabel('# clients')
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)

    x_ticks = []
    i = 0
    for ncli in nclients:
        x_pos = [xsep*i-wdth/2-sep, xsep*i+wdth/2+sep]
        x_ticks.append(xsep*i)
        j = len(drops)
        for drop in reversed(drops):
            j-=1
            means = np.array([ccs_sent_mean[10000][drop][ncli] + ccs_rcvd_mean[10000][drop][ncli], online_sent_mean[10000][drop][ncli] + online_rcvd_mean[10000][drop][ncli]])
            error = np.array([ccs_sent_std[10000][drop][ncli] + ccs_rcvd_std[10000][drop][ncli], online_sent_std[10000][drop][ncli] + online_rcvd_std[10000][drop][ncli]])
            ax.bar(x_pos, means /8/1024/1024, yerr=error/8/1024/1024, align='center', alpha=1, ecolor='black', color =clrs[j], hatch=htch,capsize=6, width=wdth)
        i+=1


    ax.set_xticks(x_ticks)
    ax.set_xticklabels(nclients)
    handles = [
        mpatches.Patch(facecolor=clrs[0][0],hatch='xx', label='CCS17'), 
        mpatches.Patch(facecolor=clrs[0][0], label='No Failures'), 
        # mpatches.Patch(facecolor=clrs[1][0],hatch='xx', label='CCS17 (With Dropouts)'), 
        mpatches.Patch(facecolor=clrs[1][0], label='With Failures'), 
    ]

    lg = fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(0.15, .85), borderaxespad=0)

        # Save the figure and show
    # plt.tight_layout()
    # plt.savefig(plots_dir + 'time_{}_{}_{}.png'.format(entity, scene, drops))
    plt.savefig(plots_dir + 'comm_clients.png', bbox_extra_artists=(lg,),bbox_inches='tight',dpi=400)


    fig, ax = plt.subplots()
    fig.set_figheight(4)
    fig.set_figwidth(8)
  
    dims = [1000, 10000, 100000]
    dimsnames = ['1K', '10K', '100K']
    ncli = 600 

    ax.set_ylabel('Data (MB)')
    ax.set_xlabel('Dimension')
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)

    x_ticks = []
    i = 0
    for dim in dims:
        x_pos = [xsep*i-wdth/2-sep, xsep*i+wdth/2+sep]
        x_ticks.append(xsep*i)
        j = len(drops)
        for drop in reversed(drops):
            j-=1
            means = np.array([ccs_sent_mean[dim][drop][ncli] + ccs_rcvd_mean[dim][drop][ncli], online_sent_mean[dim][drop][ncli] + online_rcvd_mean[dim][drop][ncli]])
            error = np.array([ccs_sent_std[dim][drop][ncli] + ccs_rcvd_std[dim][drop][ncli], online_sent_std[dim][drop][ncli] + online_rcvd_std[dim][drop][ncli]])
            ax.bar(x_pos, means/8/1024/1024, yerr=error/8/1024/1024, align='center', alpha=1, ecolor='black', color =clrs[j], hatch=htch,capsize=6, width=wdth)
        i+=1


    ax.set_xticks(x_ticks)
    ax.set_xticklabels(dimsnames)


    handles = [
        mpatches.Patch(facecolor=clrs[0][0],hatch='xx', label='CCS17'), 
        mpatches.Patch(facecolor=clrs[0][0], label='No Failures'), 
        # mpatches.Patch(facecolor=clrs[1][0],hatch='xx', label='CCS17 (With Dropouts)'), 
        mpatches.Patch(facecolor=clrs[1][0], label='With Failures'), 
    ]

    lg = fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(0.15, .85), borderaxespad=0)
        # Save the figure and show
    # plt.tight_layout()
    # plt.savefig(plots_dir + 'time_{}_{}_{}.png'.format(entity, scene, drops))
    plt.savefig(plots_dir + 'comm_dims.png', bbox_extra_artists=(lg,),bbox_inches='tight',dpi=400)


def plot_time_server(ccs, online):
    
    drops = [0.0, 0.1, 0.3]

    structdrops = {0.0:{}, 0.1:{}, 0.2:{}, 0.3:{}}
    structdata = {100000 : deepcopy(structdrops), 10000 : deepcopy(structdrops), 1000 : deepcopy(structdrops)}
   
    ccs_mean  = deepcopy(structdata)
    ccs_std = deepcopy(structdata)

    online_mean = deepcopy(structdata)
    online_std = deepcopy(structdata)

    for s in scenarios:
        if s.dimension not in structdata:
            continue

        ccs_mean[s.dimension][s.dropout][s.nclients] = np.mean(ccs[s]['round0']) + np.mean(ccs[s]['round1']) + np.mean(ccs[s]['round2']) + np.mean(ccs[s]['round4'])
        ccs_std[s.dimension][s.dropout][s.nclients] = np.std(ccs[s]['round0']) + np.std(ccs[s]['round1']) + np.std(ccs[s]['round2']) + np.std(ccs[s]['round4'])

        online_mean[s.dimension][s.dropout][s.nclients] = np.mean(online[s]['encrypt']) + np.mean(online[s]['construct'])
        online_std[s.dimension][s.dropout][s.nclients] = np.std(online[s]['encrypt']) + np.std(online[s]['construct'])


    nclients = [100, 300, 600]
    wdth = 0.15
    xsep = 1.5
    xxsep = xsep/4 
    sep = xsep /16
    xes = ['ccs17', 'online']
    clrs = [['#99CCFF', '#99CCFF'], ['#f0938a', '#f0938a'],['#B2716B','#B2716B']]
    htch = ['x', None]

    fig, ax = plt.subplots()
    fig.set_figheight(4)
    fig.set_figwidth(8)
    # ax.set_ylim(0,400)
    ax.set_ylabel('seconds')
    ax.set_xlabel('# clients')
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)

    x_ticks = []
    i = 0
    for ncli in nclients:
        x_ticks.append(xsep*i)
        j = 0
        for drop in drops:
            k = j-1
            x_pos = [xsep*i+k*xxsep-sep,xsep*i+k*xxsep+sep]
            means = np.array([ccs_mean[10000][drop][ncli], online_mean[10000][drop][ncli]])
            error = np.array([ccs_std[10000][drop][ncli], online_std[10000][drop][ncli]])
            ax.bar(x_pos, means, yerr=error, align='center', alpha=1, ecolor='black', color =clrs[j], hatch=htch,capsize=6, width=wdth)
            # print(ncli, drop, means[0]/means[1])

            j+=1
        i+=1


    ax.set_xticks(x_ticks)
    ax.set_xticklabels(nclients)

    handles = [
        mpatches.Patch(facecolor='white', hatch='xx', label='CCS17'), 
        mpatches.Patch(facecolor=clrs[0][0], label='Failures = 0%'), 
        # mpatches.Patch(facecolor=clrs[1][0],hatch='xx', label='CCS17 (With Dropouts)'), 
        mpatches.Patch(facecolor=clrs[1][0], label='Failures = 10%'), 
        mpatches.Patch(facecolor=clrs[2][0], label='Failures = 30%'), 
    ]

    lg = fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(0.15, .85), borderaxespad=0)

    plt.savefig(plots_dir + 'time_server_clients.png', bbox_extra_artists=(lg,),bbox_inches='tight',dpi=400)


    fig, ax = plt.subplots()
    fig.set_figheight(4)
    fig.set_figwidth(8)
  
    dims = [1000, 10000, 100000]
    dimsnames = ['1K', '10K', '100K']
    ncli = 600 

    ax.set_ylabel('seconds')
    ax.set_xlabel('Dimension')
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    # ax.set_ylim(0,400)

    x_ticks = []
    i = 0
    for dim in dims:
        x_pos = [xsep*i-wdth/2-sep, xsep*i+wdth/2+sep]
        x_ticks.append(xsep*i)
        j = 0
        for drop in drops:
            k = j-1
            x_pos = [xsep*i+k*xxsep-sep,xsep*i+k*xxsep+sep]
            means = np.array([ccs_mean[dim][drop][ncli], online_mean[dim][drop][ncli]])
            error = np.array([ccs_std[dim][drop][ncli], online_std[dim][drop][ncli]])
            ax.bar(x_pos, means, yerr=error, align='center', alpha=1, ecolor='black', color =clrs[j], hatch=htch,capsize=6, width=wdth)
            j+=1
        i+=1


    ax.set_xticks(x_ticks)
    ax.set_xticklabels(dimsnames)


    handles = [
        mpatches.Patch(facecolor='white', hatch='xx', label='CCS17'), 
        mpatches.Patch(facecolor=clrs[0][0], label='Failures = 0%'), 
        # mpatches.Patch(facecolor=clrs[1][0],hatch='xx', label='CCS17 (With Dropouts)'), 
        mpatches.Patch(facecolor=clrs[1][0], label='Failures = 10%'), 
        mpatches.Patch(facecolor=clrs[2][0], label='Failures = 30%'), 
    ]

    lg = fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(0.15, .85), borderaxespad=0)

    plt.savefig(plots_dir + 'time_server_dims.png', bbox_extra_artists=(lg,),bbox_inches='tight',dpi=400)


def get_time_ms(setup, online, entity):
    structdrops = {0.0:{}, 0.1:{}, 0.2:{}, 0.3:{}}
    structdata = {100000 : deepcopy(structdrops), 10000 : deepcopy(structdrops), 1000 : deepcopy(structdrops)}

    setup_mean = deepcopy(structdata)
    online_mean = deepcopy(structdata)

    for s in scenarios:
        if s.dimension not in structdata:
            continue

        if entity == "client":
            setup_mean[s.dimension][s.dropout][s.nclients] =( 1000* np.mean(setup[s]['register']) , 1000* np.mean(setup[s]['keysetup1']) + 1000* np.mean(setup[s]['keysetup2']))
        else:
            setup_mean[s.dimension][s.dropout][s.nclients] =( 1000* np.mean(setup[s]['register']) , 1000* np.mean(setup[s]['keysetup']))

        online_mean[s.dimension][s.dropout][s.nclients] =( 1000* np.mean(online[s]['encrypt']) , 1000* np.mean(online[s]['construct']))

    print(entity + " runtime measurements:")
    print("-------------------------")
    print("100 clients, 1K dim:")
    print("00% failures :  Setup = ",setup_mean[1000][0.0][100])
    print("00% failures :  Online = ",online_mean[1000][0.0][100])
    print("10% failures :  Setup = ",setup_mean[1000][0.1][100])
    print("10% failures :  Online = ",online_mean[1000][0.1][100])
    print("30% failures :  Setup = ",setup_mean[1000][0.3][100])
    print("30% failures :  Online = ",online_mean[1000][0.3][100])
    print() 

    print("300 clients, 1K dim:")
    print("00% failures :  Setup = ",setup_mean[1000][0.0][300])
    print("00% failures :  Online = ",online_mean[1000][0.0][300])
    print("10% failures :  Setup = ",setup_mean[1000][0.1][300])
    print("10% failures :  Online = ",online_mean[1000][0.1][300])
    print("30% failures :  Setup = ",setup_mean[1000][0.3][300])
    print("30% failures :  Online = ",online_mean[1000][0.3][300])
    print() 

    print("600 clients, 1K dim:")
    print("00% failures :  Setup = ",setup_mean[1000][0.0][600])
    print("00% failures :  Online = ",online_mean[1000][0.0][600])
    print("10% failures :  Setup = ",setup_mean[1000][0.1][600])
    print("10% failures :  Online = ",online_mean[1000][0.1][600])
    print("30% failures :  Setup = ",setup_mean[1000][0.3][600])
    print("30% failures :  Online = ",online_mean[1000][0.3][600])
    print() 

    print("100 clients, 10K dim:")
    print("00% failures :  Setup = ",setup_mean[10000][0.0][100])
    print("00% failures :  Online = ",online_mean[10000][0.0][100])
    print("10% failures :  Setup = ",setup_mean[10000][0.1][100])
    print("10% failures :  Online = ",online_mean[10000][0.1][100])
    print("30% failures :  Setup = ",setup_mean[10000][0.3][100])
    print("30% failures :  Online = ",online_mean[10000][0.3][100])
    print() 

    print("300 clients, 10K dim:")
    print("00% failures :  Setup = ",setup_mean[10000][0.0][300])
    print("00% failures :  Online = ",online_mean[10000][0.0][300])
    print("10% failures :  Setup = ",setup_mean[10000][0.1][300])
    print("10% failures :  Online = ",online_mean[10000][0.1][300])
    print("30% failures :  Setup = ",setup_mean[10000][0.3][300])
    print("30% failures :  Online = ",online_mean[10000][0.3][300])
    print() 

    print("600 clients, 10K dim:")
    print("00% failures :  Setup = ",setup_mean[10000][0.0][600])
    print("00% failures :  Online = ",online_mean[10000][0.0][600])
    print("10% failures :  Setup = ",setup_mean[10000][0.1][600])
    print("10% failures :  Online = ",online_mean[10000][0.1][600])
    print("30% failures :  Setup = ",setup_mean[10000][0.3][600])
    print("30% failures :  Online = ",online_mean[10000][0.3][600])

    print("100 clients, 100K dim:")
    print("00% failures :  Setup = ",setup_mean[100000][0.0][100])
    print("00% failures :  Online = ",online_mean[100000][0.0][100])
    print("10% failures :  Setup = ",setup_mean[100000][0.1][100])
    print("10% failures :  Online = ",online_mean[100000][0.1][100])
    print("30% failures :  Setup = ",setup_mean[100000][0.3][100])
    print("30% failures :  Online = ",online_mean[100000][0.3][100])
    print() 

    print("300 clients, 100K dim:")
    print("00% failures :  Setup = ",setup_mean[100000][0.0][300])
    print("00% failures :  Online = ",online_mean[100000][0.0][300])
    print("10% failures :  Setup = ",setup_mean[100000][0.1][300])
    print("10% failures :  Online = ",online_mean[100000][0.1][300])
    print("30% failures :  Setup = ",setup_mean[100000][0.3][300])
    print("30% failures :  Online = ",online_mean[100000][0.3][300])
    print() 

    print("600 clients, 100K dim:")
    print("00% failures :  Setup = ",setup_mean[100000][0.0][600])
    print("00% failures :  Online = ",online_mean[100000][0.0][600])
    print("10% failures :  Setup = ",setup_mean[100000][0.1][600])
    print("10% failures :  Online = ",online_mean[100000][0.1][600])
    print("30% failures :  Setup = ",setup_mean[100000][0.3][600])
    print("30% failures :  Online = ",online_mean[100000][0.3][600])
    print() 
    print() 


def get_comm(setup_sent,setup_rcvd, online_sent,online_rcvd):
    structdrops = {0.0:{}, 0.1:{}, 0.2:{}, 0.3:{}}
    structdata = {100000 : deepcopy(structdrops), 10000 : deepcopy(structdrops), 1000 : deepcopy(structdrops)}

    setup_sent_mean = deepcopy(structdata)
    setup_rcvd_mean = deepcopy(structdata)
    online_sent_mean = deepcopy(structdata)
    online_rcvd_mean = deepcopy(structdata)

    for s in scenarios:
        if s.dimension not in structdata:
            continue

        setup_sent_mean[s.dimension][s.dropout][s.nclients] =( np.mean(setup_sent[s]['register']) /8/1024, np.mean(setup_sent[s]['keysetup1'])/8/1024 )
        setup_rcvd_mean[s.dimension][s.dropout][s.nclients] =(0, np.mean(setup_rcvd[s]['keysetup1'])/8/1024 + np.mean(setup_rcvd[s]['keysetup2'])/8/1024)

        online_sent_mean[s.dimension][s.dropout][s.nclients] = (np.mean(online_sent[s]['encrypt'])/8/1024, np.mean(online_sent[s]['construct'])/8/1024)
        online_rcvd_mean[s.dimension][s.dropout][s.nclients] = (0,np.mean(online_rcvd[s]['construct'])/8/1024)

    print("Bandwidth measurements:")
    print("-------------------------")
    # for n in [100,300,600]:
    #     for d in [0.0,0.3]:
    #         print("nclients={}, drops={}".format(n,d))
    #         print("{:.2f} KB & {:.2f} KB & {:.2f} KB & {:.2f} KB".format(sS[0],sS[1],oS[0],oS[1]))
    #         print("{:.2f} KB & {:.2f} KB & {:.2f} KB & {:.2f} KB".format(sR[0],sR[1],oR[0],oR[1]))
    #         print("{:.2f} KB & {:.2f} KB & {:.2f} KB & {:.2f} KB".format(sS[0]+sR[0],sS[1]+sR[1],oS[0]+oR[0],oS[1]+oR[1]))
    #         print()

#     for d in [0.0,0.3]:
    for dim in [1000,10000,100000]:
        for n in [100,300,600]:
            print("{} clients, {}K dim, 00% fail:".format(n,int(dim/1000)))
            sS = setup_sent_mean[dim][0.0][n]
            oS = online_sent_mean[dim][0.0][n]
            sR = setup_rcvd_mean[dim][0.0][n]
            oR = online_rcvd_mean[dim][0.0][n]
            print("00% failures : Sent = {:.2f} KB & {:.2f} KB & {:.2f} KB & {:.2f} KB".format(sS[0],sS[1],oS[0],oS[1]))
            print("00% failures : Rcvd = {:.2f} KB & {:.2f} KB & {:.2f} KB & {:.2f} KB".format(sR[0],sR[1],oR[0],oR[1]))
            print("00% failures : Totl = {:.2f} KB & {:.2f} KB & {:.2f} KB & {:.2f} KB".format(sS[0]+sR[0],sS[1]+sR[1],oS[0]+oR[0],oS[1]+oR[1]))
            sS = setup_sent_mean[dim][0.1][n]
            oS = online_sent_mean[dim][0.1][n]
            sR = setup_rcvd_mean[dim][0.1][n]
            oR = online_rcvd_mean[dim][0.1][n]
            print("10% failures : Sent = {:.2f} KB & {:.2f} KB & {:.2f} KB & {:.2f} KB".format(sS[0],sS[1],oS[0],oS[1]))
            print("10% failures : Rcvd = {:.2f} KB & {:.2f} KB & {:.2f} KB & {:.2f} KB".format(sR[0],sR[1],oR[0],oR[1]))
            print("10% failures : Totl = {:.2f} KB & {:.2f} KB & {:.2f} KB & {:.2f} KB".format(sS[0]+sR[0],sS[1]+sR[1],oS[0]+oR[0],oS[1]+oR[1]))
            print()

            sS = setup_sent_mean[dim][0.0][n]
            oS = online_sent_mean[dim][0.0][n]
            sR = setup_rcvd_mean[dim][0.0][n]
            oR = online_rcvd_mean[dim][0.0][n]
            print("30% failures : Sent = {:.2f} KB & {:.2f} KB & {:.2f} KB & {:.2f} KB".format(sS[0],sS[1],oS[0],oS[1]))
            print("30% failures : Rcvd = {:.2f} KB & {:.2f} KB & {:.2f} KB & {:.2f} KB".format(sR[0],sR[1],oR[0],oR[1]))
            print("30% failures : Totl = {:.2f} KB & {:.2f} KB & {:.2f} KB & {:.2f} KB".format(sS[0]+sR[0],sS[1]+sR[1],oS[0]+oR[0],oS[1]+oR[1]))
            print()





    
if __name__ == "__main__":
    _, ccs_client_time, _, ccs_server_time = parsetime(ccs_data_dir)
    _, _, ccs_sent_comm, ccs_rcvd_comm = parsecomm(ccs_data_dir)
    
    client_setup_time, client_online_time, server_setup_time, server_online_time = parsetime(ours_data_dir)
    sent_setup_comm, rcvd_setup_comm, sent_online_comm,  rcvd_online_comm = parsecomm(ours_data_dir)
    
    plot_time_client(ccs_client_time, client_online_time)
    plot_comm(ccs_sent_comm, ccs_rcvd_comm, sent_online_comm,  rcvd_online_comm)
    plot_time_server(ccs_server_time, server_online_time)


    get_time_ms(server_setup_time, server_online_time, "server")
    get_time_ms(client_setup_time, client_online_time, "client")
    get_comm(sent_setup_comm, rcvd_setup_comm, sent_online_comm,  rcvd_online_comm)

