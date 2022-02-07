""" 
### **Extra Utilities**

This module contain additional utility methods used in the building blocks and the protocols"""

import gmpy2, random


def add_vectors(A,B,r):
    """Adds two vectors mod r"""
    C=[]
    for a,b in zip(A,B):
        C.append((a+b) % r)
    return C

def subs_vectors(A,B,r):
    """Substracts two vectors mod r"""

    C=[]
    for a,b in zip(A,B):
        C.append((a-b) % r)
    return C

def getprimeover(bits):
    """Returns a prime number with specific number of bits """

    randfunc = random.SystemRandom()
    r = gmpy2.mpz(randfunc.getrandbits(bits))
    r = gmpy2.bit_set(r, bits - 1)
    return gmpy2.next_prime(r)



def invert(a, b):
    """Finds the invers of a mod b"""
    s = gmpy2.invert(a, b)
    # according to documentation, gmpy2.invert might return 0 on
    # non-invertible element, although it seems to actually raise an
    # exception; for consistency, we always raise the exception
    if s == 0:
        raise ZeroDivisionError('invert() no inverse exists')
    return s

def powmod(a, b, c):
    """Computes a to the power of b mod c"""

    if a == 1:
        return 1
    return gmpy2.powmod(a, b, c)



class PField(object):
    """A field \\(\\mathbb{Z}_p\\) of all the integers mod \\(p\\)"""
    def __init__(self, encoded_value, p, bits):
        """Initialize a Field element to a certain value.

        The value passed as parameter is internally encoded as
        a mpz.
        """
        self.p = p
        self.bits = bits
        if  isinstance(encoded_value, gmpy2.mpz):
            self._value = encoded_value
        elif isinstance(encoded_value, int):
            self._value = gmpy2.mpz(encoded_value)
        elif isinstance(encoded_value, bytes):
            self._value = gmpy2.mpz(int.from_bytes(encoded_value,"big"))
        else:
            raise ValueError("The encoded value is of type {} but it must be an integer or a byte string".format(type(encoded_value)))

    def __eq__(self, other):
        return self._value == other._value

    def __int__(self):
        """Return the field element, encoded as a 1024-bit integer."""
        return self._value


    def __hash__(self):
        return self._value.__hash__()

    def encode(self):
        """Return the field element, encoded as a 256 byte string."""
        return self._value.to_bytes(256, "big")

    def __mul__(self, factor):

       return PField((self._value * factor._value) % self.p,self.p, self.bits)

    def __add__(self, term):
        return PField((self._value + term._value) % self.p,self.p, self.bits)

    def __sub__(self, term):
        return PField((self._value - term._value) % self.p,self.p, self.bits)


    def inverse(self):
        """Return the inverse of this element in Zp."""
        if self._value == 0:
            raise ValueError("Inversion of zero")

        return PField(invert(self._value, self.p),self.p, self.bits)
    def __pow__(self, exponent):
        return PField(powmod(self._value, exponent._value, self.p),self.p, self.bits)

    def __mod__(self, mod):
        return PField(self._value % mod._value,self.p, self.bits)


class P2048Field(PField):
    """A Field using the 16th Mersenne prime \\(p=2^{2203} - 1\\) used to perform field operation on 2048 bits numbers"""
    bits = 2048
    def __init__(self, encoded_value):
        super().__init__(encoded_value, 2**2203 - 1, P2048Field.bits)

class P1024Field(PField):
    """A Field using the 15th Mersenne prime \\(p=2^{1279} - 1\\) used to perform field operation on 1024 bits numbers"""
    bits = 1024
    def __init__(self, encoded_value):
        super().__init__(encoded_value, 2**1279 - 1, P1024Field.bits)

class P512Field(PField):
    """A Field using the 13th Mersenne prime \\(p=2^{521} - 1\\) used to perform field operation on 512 bits numbers"""

    bits = 512
    def __init__(self, encoded_value):
        super().__init__(encoded_value,2**521 - 1, P512Field.bits)
 
class P256Field(PField):
    """A Field using the prime \\(p=2^{257} - 2233\\) used to perform field operation on 256 bits numbers"""

    # 2**n - k
    bits = 256
    def __init__(self, encoded_value):
        super().__init__(encoded_value,2**257 - 2233, P256Field.bits)
      
class P128Field(PField):
    """A Field using the prime \\(p=2^{129} - 1365\\) used to perform field operation on 128 bits numbers"""

    # 2**n - k
    bits = 128
    def __init__(self, encoded_value):
        super().__init__(encoded_value,2**129 - 1365, P128Field.bits)
       
class P64Field(PField):
    """A Field using the prime \\(p=2^{65} - 493\\) used to perform field operation on 64 bits numbers"""

    # 2**n - k
    bits = 64
    def __init__(self, encoded_value):
        super().__init__(encoded_value,2**65 - 493, P64Field.bits)
