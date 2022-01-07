import random
from Crypto.Cipher.AES import key_size
from gmpy2 import mpz, rint_round, log2

from protocols.buildingblocks.utils import getprimeover, invert, powmod
from protocols.buildingblocks.VectorEncoding import VES
from protocols.buildingblocks.FullDomainHash import FDH

DEFAULT_KEY_SIZE = 2048

class PublicParam(object):
    def __init__(self, n, bits, H) -> None:
        super().__init__()
        self.n = n
        self.nsquare = n * n
        self.bits = bits
        self.H = H

    def __eq__(self, other):
        return self.n == other.n

    def __repr__(self):
        hashcode = hex(hash(self.H))
        nstr = self.n.digits()
        return "<PublicParam (N={}...{}, H(x)={})>".format(nstr[:5],nstr[-5:],hashcode[:10])

class EncryptedNumber(object):
    def __init__(self, param, ciphertext) -> None:
        super().__init__()
        self.pp = param
        self.ciphertext = ciphertext
    
    def __add__(self, other):
        if isinstance(other, EncryptedNumber):
            return self._add_encrypted(other)
        if isinstance(other, mpz):
            e = EncryptedNumber(self.pp, other)
            return self._add_encrypted(e)
    
    def __iadd__(self, other):
        if isinstance(other, EncryptedNumber):
            return self._add_encrypted(other)
        if isinstance(other, mpz):
            e = EncryptedNumber(self.pp, other)
            return self._add_encrypted(e)

    def __repr__(self):
        estr = self.ciphertext.digits()
        return "<EncryptedNumber {}...{}>".format(estr[:5],estr[-5:])

    def _add_encrypted(self, other):
        if self.pp != other.pp:
            raise ValueError("Attempted to add numbers encrypted against "
                             "different prameters!")

        return EncryptedNumber(self.pp, self.ciphertext * other.ciphertext % self.pp.nsquare)

    def getrealsize(self):
        return self.pp.bits*2

class ServerKey(object):
    def __init__(self, param, key, VE) -> None:
        super().__init__()
        self.pp = param
        self.s = key
        self.VE = VE

    def __repr__(self):
        hashcode = hex(hash(self))
        return "<ServerKey {}>".format(hashcode[:10])

    def __eq__(self, other):
        return (self.pp == other.pp and self.s == other.s )

    def __hash__(self):
        return hash(self.s)

    def decrypt_vector(self, cipherv:EncryptedNumber,  t, delta = None) -> int:
        counter = 0
        V = []
        for c in cipherv:
            V.append(self.decrypt(c, (counter << self.pp.bits // 2) | t, delta))
            counter +=1
        
        return self.VE.decode(V)

    def decrypt(self, cipher:EncryptedNumber, t, delta=None) -> int:
        if not isinstance(cipher, EncryptedNumber):
            raise TypeError('Expected encrypted number type but got: %s' %
                            type(cipher))
        if self.pp != cipher.pp:
            raise ValueError('encrypted_number was encrypted against a '
                             'different key!')
        return self.raw_decrypt(cipher.ciphertext, t, delta)
    

    def raw_decrypt(self, ciphertext:int, t, delta=None):
        if not isinstance(ciphertext, mpz):
            raise TypeError('Expected mpz type ciphertext but got: %s' %
                        type(ciphertext))
        V = (ciphertext * powmod(self.pp.H(t), self.s, self.pp.nsquare)) % self.pp.nsquare
        # V = (ciphertext * self.pp.H(t, self.s)) % self.pp.nsquare
        X = self.l_function(V, self.pp.n)  % self.pp.n
        if delta:
            X = (X * invert(delta, self.pp.nsquare)) % self.pp.n
        return int(X)
    
    def l_function(self, x, p):
        return (x - 1) // p


class UserKey(object):
    def __init__(self, index, param, key, VE) -> None:
        super().__init__()
        self.i = index
        self.pp = param
        self.s = key
        self.max_int = self.pp.n // 3 - 1
        self.VE = VE


    def __repr__(self):
        hashcode = hex(hash(self))
        return "<UserKey {}>".format(hashcode[:10])

    def __eq__(self, other):
        return (self.pp == other.pp and self.s == other.s )

    def __hash__(self):
        return hash(self.s)

    def encrypt(self, plaintext: int, t) -> EncryptedNumber:
        # if not isinstance(plaintext, int):
        #     raise TypeError('Expected int type plaintext but got: %s' %
        #                     type(plaintext))

        # if self.pp.n - self.max_int <= plaintext < self.pp.n:
        #     # Very large plaintext, take a sneaky shortcut using inverses
        #     neg_plaintext = self.pp.n - plaintext  # = abs(plaintext - nsquare)
        #     neg_ciphertext = (self.pp.n * neg_plaintext + 1) % self.pp.nsquare
        #     nude_ciphertext = invert(neg_ciphertext, self.pp.nsquare)
        # else:
            # we chose g = n + 1, so that we can exploit the fact that
            # (n+1)^plaintext = n*plaintext + 1 mod n^2
        nude_ciphertext = (self.pp.n * plaintext + 1) % self.pp.nsquare
        r = powmod(self.pp.H(t), self.s, self.pp.nsquare)
        # r = self.pp.H(t,self.s)
        ciphertext = (nude_ciphertext * r) % self.pp.nsquare
        return EncryptedNumber(self.pp, ciphertext)

    def encrypt_vector(self, vector: int, t) -> EncryptedNumber:
        V = self.VE.encode(vector)
        counter = 0
        E = []
        for v in V:
            E.append(self.encrypt(v, (counter << self.pp.bits // 2) | t))

            counter += 1
        return E


class JLS(object):
    inputsize = 16
    inputdimension = 1
    def __init__(self, nusers, inputsize, inputdimension, keysize = DEFAULT_KEY_SIZE) -> None:
        super().__init__()
        self.nusers = nusers
        self.keysize = keysize
        self.n_length = keysize // 2
        self.inputsize = inputsize 
        self.inputdimension = inputdimension 
        self.VE = VES(self.n_length, self.nusers, self.inputsize, self.inputdimension)

    def setinputdimension(self, vs):
        self.inputdimension = vs
        self.VE.setvectorsize(self.inputdimension)

    def generate_keys(self):
        p = q = n = None
        n_len = 0
        while n_len != self.n_length:
            p = getprimeover(self.n_length // 2)
            q = p
            while q == p:
                q = getprimeover(self.n_length // 2)
            n = p * q
            n_len = n.bit_length()

        # def H( t:int):
        #     # r = (1+t_period*n) % (n*n)
        #     r = (powmod(t,n,n*n)) % (n*n)

        #     return r

        fdh = FDH(self.keysize, n*n)


        public_param = PublicParam(n, self.n_length, fdh.H)
        
        seed = random.SystemRandom()
        s0 = mpz(0)
        users = {}
        
        for i in range(self.nusers):
            index = i+1
            s = mpz(seed.getrandbits(2*n_len))
            users[i] = UserKey(index, public_param, s, self.VE)
            s0+=s
        s0 = -s0
        server = ServerKey(public_param, s0, self.VE)


        return public_param, server, users

    def aggregate(self,e):
        assert len(e) > 0 , "empty list of ciphers to aggregate"
        c = e[0]
        for k in e[1:]:
            c += k
        return c


    def aggregate_vector(self, ev):
        assert len(ev) > 0 , "empty list of ciphers to aggregate"
        l = len(ev[0])
        for v in ev:
            assert l == len(v), "attempting to aggregate encrypted vectors of different size"
        
        C=[]
        for counter in range(l):
            c = ev[0][counter]
            for v in ev[1:]:
                c += v[counter]
            C.append(c)
        return C
