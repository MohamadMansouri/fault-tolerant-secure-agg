"""
### ** Pseudo-Random Generator **

This module contains a wraper for AES-CTR encryption from the library \"[Python Cryptography Toolkit (pycrypto)](https://cryptography.io/en/latest/)\"
"""
from Crypto.Cipher import AES
from math import ceil
from gmpy2 import mpz

class PRG(object):
    """
    A pseudo-random generator class used to extend an integer to a vector

    ## **Args**:
    -------------
    *vectorsize* : `int` --
        the number of elements of the output vector

    *elementsize* : `int` --
        the size of each element of the vector in bits

    ## **Attributes**:
    -------------
    *m* : `int` --
        the number of elements of the output vector ( \\(m\\))

    *bits* : `int` --
        the size of each element of the vector ( \\(bits\\))
    
    *e* : `int` --
        the size of each element of the vector in bytes
    """
    _zero=0
    _nonce = _zero.to_bytes(12,"big")
    security = 128
    """The bitlength of the input of the PRG"""
    def __init__(self, vectorsize, elementsize) -> None:
        super().__init__()
        self.m = vectorsize
        self.bits = elementsize
        self.e = ceil(elementsize / 8)

    def eval(self,x):
        """Computes AES-CTR of an empty string of size equal \\(m \\times bits\\) and then splits the result to generate a vector.
        
        It returns a vector of \\(m\\) elements each of size \\(bits\\) bits
        """
        seed = x
        if isinstance(seed, mpz):
            seed = int(x)
        if isinstance(seed, int):
            if seed >= 2**PRG.security:
                mask = 2**PRG.security - 1
                seed  &= mask 
            seed = seed.to_bytes(PRG.security // 8, "big")
        elif not isinstance(seed, bytes):
            raise ValueError("seed should be of type either int or bytes")

        c = AES.new(seed[:PRG.security // 8], AES.MODE_CTR, nonce=PRG._nonce, initial_value=0)
        cipher = c.encrypt(b''.rjust(self.e*self.m, b'\x00'))
        return [int.from_bytes(cipher[i:i+self.e],"big") % 2**self.bits for i in range(0,len(cipher), self.e)]
