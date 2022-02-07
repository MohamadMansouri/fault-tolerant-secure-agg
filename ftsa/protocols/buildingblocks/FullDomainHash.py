"""
### **Full-Domain Hash**

This module computes a full domain hash value usign SHA256 hash function
"""

from Crypto.Hash import SHA256
from gmpy2 import mpz, gcd



class FDH(object):
    """
    The Full-Domain Hash scheme

    ## **Args**:
    -------------
    *bitsize* : `int` -- 
        The bitlength of the output of the FDH
    
    *N* : `int` -- 
        The modulus \\(N\\) such that the FDH output is in \\(\\mathbb{Z}^*_N\\) 

    """
    def __init__(self, bitsize, N) -> None:
        super().__init__()
        self.bitsize = bitsize
        self.N = N

    def H(self, t):
        """
        Computes the FDH using SHA256
        
        It computes:
            $$\\textbf{SHA256}(x||0) ||\\textbf{SHA256}(x||1) || ... || \\textbf{SHA256}(x||c) \\mod N$$
        where \\(c\\) is a counter that keeps incrementing until the size of the output has *bitsize* length and the output falls in  \\(\\mathbb{Z}^*_N\\)

        ## **Args**:
        -------------
        *t* : `int` -- 
            The input of the hash function

        ## **Returns**:
        ----------------
        A value in \\(\\mathbb{Z}^*_N\\) of type `gmpy2.mpz`
        """
        counter = 1
        result = b''
        while True:
            while True:
                h = SHA256.new()
                h.update(int(t).to_bytes(self.bitsize // 2,"big") + counter.to_bytes(1,"big"))
                result += h.digest()
                counter += 1
                if len(result) < (self.bitsize // 8):
                    break
            r = mpz(int.from_bytes(result[-self.bitsize:],"big"))
            if gcd(r, self.N) == 1:
                break
            else:
                print("HAPPENED")
        return r
