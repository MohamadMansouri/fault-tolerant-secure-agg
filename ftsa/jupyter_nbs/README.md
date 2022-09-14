# Tests using Jupyter Notebook 

To run the tests, open these files in a Jupyter notebook. Please make sure that you open the notebook from your shell while activating the virtual environment `.venv` (where ftsa package is installed). Otherwise, you have to manually set the kernel of your notebook to the python executable in `.venv`.


### Notebook "test_buildingblocks.ipynb"
This notebook contains tests of each of the cryptographic building blocks used to implement our protocol. The building blocks are:
- Shamir Secret Sharing (see section 3.2 in the manuscript)
- Shamir Secret Sharing over the Integers (see section 3.3 in the manuscript)
- AES-GCM Authenticated Encryption (see section 3.5 in the manuscript)
- Vector Encoding Scheme (see section 6.2 in the manuscript)
- Pseudo-Random Generator (see section 3.1 in the manuscript)

### Notebook "test_JL.ipynb"
This notebook contains tests of [Joye-Libert secure aggregation scheme](https://link.springer.com/chapter/10.1007/978-3-642-39884-1_10) (see section 3.6 in the manuscript). The notebook contains tests for running JL scheme with integer inputs and with vector inputs.

### Notebook "test_TJL.ipynb"
This notebook contains tests of the threshold variant of JL secure aggregation scheme presented in our work (see section 5 in the manuscript). The notebook contains tests for running TJL scheme with integer inputs

### Notebook "test_TJL_vectors.ipynb"
This notebook contains tests of the threshold variant of JL secure aggregation scheme presented in our work (see section 5 in the manuscript). The notebook contains tests for running TJL scheme with vector inputs

### Notebook "test_ccs17protocol.ipynb"
This notebook contains tests of our implementation of [SecAgg](https://dl.acm.org/doi/10.1145/3133956.3133982).
We create the aggregator and some clients of SecAgg protocol and we run all the protocol rounds sequentially.

### Notebook "test_ourprotocol.ipynb"
This notebook contains tests of the implementation of our protocol.
We create the aggregator and some clients of our protocol and we run all the protocol rounds sequentially.
