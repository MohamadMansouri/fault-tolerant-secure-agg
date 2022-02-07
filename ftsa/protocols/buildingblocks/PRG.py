from Crypto.Cipher import AES
from math import ceil
from gmpy2 import mpz

class PRG(object):
    zero=0
    nonce = zero.to_bytes(12,"big")
    security = 128
    def __init__(self, vectorsize, elementsize) -> None:
        super().__init__()
        self.m = vectorsize
        self.bits = elementsize
        self.e = ceil(elementsize / 8)

    def eval(self,x):
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

        c = AES.new(seed[:PRG.security // 8], AES.MODE_CTR, nonce=PRG.nonce, initial_value=0)
        cipher = c.encrypt(b''.rjust(self.e*self.m, b'\x00'))
        return [int.from_bytes(cipher[i:i+self.e],"big") % 2**self.bits for i in range(0,len(cipher), self.e)]
