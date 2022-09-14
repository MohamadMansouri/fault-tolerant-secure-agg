# Benchmarks
Here you can find the python script that will run an end-to-end execution of the protocols and measure the time cost and the communication cost. The elapsed time of execution of each protocol phase is measured using `time` python library. The communication cost is measured by counting the raw size of the data that should be transmitted on the network (We do not perform real network transmission, instead we pass the data between the parties by running the clients and the aggregator in the same process). 

### Benchmarking SecAgg
To run the benchmarks of SecAgg, run `benchmarks_css17.py` (make sure to run them from `.venv`):
```
Usage: benchmarks_ccs17.py <time_benchmarks.csv> <comm_benchmarks.csv> [comma separated run numbers (no spaces)]
	 use [-p] to only see the existing runs
```

### Benchmarking Our Protocol
To run the benchmarks of our protocol, run `benchmarks_ours.py` (make sure to run them from `.venv`):
```
Usage: benchmarks_ours.py <time_benchmarks.csv> <comm_benchmarks.csv> [comma separated run numbers (no spaces)]
	 use [-p] to only see the existing runs
```

### Important Note
Each benchmark involves running all the clients and the aggregator in one process. This means that your processor will execute the code of each client sequentially and then the aggregator code. This is performed for each protocol round. Hence, when you execute the benchmarks on your machine (with hundreds of clients) you should expect it to take long time (running all the benchmarks takes more than one day) 

### Benchmarks results 
We give the raw data of the benchmark results in [results](results). The python script `visualize_benchmarks.py` helps visualize the results. The script plots graphs in [plots](plots) and prints the mean of the results in the terminal.
These results are presented in section 9 of the manuscript.
