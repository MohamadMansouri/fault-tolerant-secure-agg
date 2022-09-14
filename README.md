# Secure and Fault-Tolerant Secure Aggregation


## Description of the project
FTSA is a protocol to securely aggregate (sum) vectors from multiple clients. The aggregation is performed at a server which we call the aggregator.
The protocol has two main interesting properties:

- **Privacy**: It preserves the privacy of the clients since it does not leak any information about the users' vectors except their sum.

- **Fault-Tolerance**: The aggregator can compute the aggregate of the clients' vectors even if some clients drop from the protocol at any point in time. 

A detailed description and evaluation of the protocol are submitted as a technical paper to ACSAC conference. The submitted manuscript can be found @ [docs/acsac-submission.pdf](docs/acsac-submission.pdf)


## What does this repository contain?
In this repository, you can find:

- The source code of our protocol (can be found @ [ftsa/protocols](ftsa/protocols)):
    - The building blocks used to construct the protocol
    - A prototype implementation of our protocol 
    - A prototype implementation of [SecAgg](https://dl.acm.org/doi/10.1145/3133956.3133982), the state-of-the-art for fault-tolerant secure aggregation protocols.

- Documentation of the source code with a detailed description of all the classes and methods. It can be found @ [docs/html](docs/html). 

- Six Jupyter notebooks that allow the user to test our protocol (and SecAgg protocol). 
They can be found @ [ftsa/jupyter_nb](ftsa/jupyter_nb). 

- Benchmarks of both our protocol and SecAgg with different parameters. Also, a visualization of the benchmark results. 
They can be found @ [ftsa/benchmarks](ftsa/benchmarks). 

## Setup of the project
The project requires a python version higher than 3.8 and a Jupyter notebook client (you can install one by running `pip install notebook`).

 
- First create a python virtual environment and activate it as follows:
```
virtualenv .venv
source .venv/bin/active
``` 
- Then launch the setup as follows:
```
python setup.py build
python setup.py install
```

## Running the notebooks
Please refer to [here](ftsa/jupyter_nbs)


## Running the benchmarks
Please refer to [here](ftsa/benchmarks)
