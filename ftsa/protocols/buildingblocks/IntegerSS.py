from os import urandom as rng
from math import factorial, log2

from ftsa.protocols.buildingblocks.ShamirSS import Share
from ftsa.protocols.buildingblocks.utils import powmod
from ftsa.protocols.buildingblocks.FullDomainHash import FDH
from ftsa.protocols.utils.CommMeasure import User

class IShare(Share):
    bits = 0
    def __init__(self, idx, value) -> None:
        super().__init__(idx, value)
    def __add__(self, other):
        assert self.idx == other.idx, "Adding shares of different indexs"
        return IShare(self.idx, self.value + other.value)
    
    def getrealsize(self):
        return User.size + IShare.bits 
    


class ISSS(object):
    def __init__(self, bitlength, sigma):
        super().__init__()
        self.bitlength = bitlength
        self.sigma = sigma


    def Share(self,secret,t,U):

        delta = factorial(len(U))
        coeffs = []
        bits = (self.bitlength + log2(delta**2) + self.sigma)
        IShare.bits = bits
        nbbytes = int( bits / 8)
        for _ in range(t-1):
            sign = 1
            if int.from_bytes(rng(1),"big") % 2 == 0:
                sign = -1
                coeff = sign * int.from_bytes(rng(nbbytes),"big")
                coeffs.append(coeff)

        coeffs.append(secret * delta)

        # Each share is y_i = p(x_i) where x_i is the public index
        # associated to each user in U.

        def make_share(idx, coeffs):
            share = 0
            for coeff in coeffs:
                share = idx * share + coeff
            return share
        return [IShare(i, make_share(i, coeffs)) for i in U]
    
    def Recon(self, shares, t, delta):
        assert len(shares) > 0 , "empty list of shares to reconstruct from"
        if isinstance(shares[0], list):
            l = len(shares[0])
            for vshare in shares:
                assert l == len(vshare), "shares of the vector does not have the same size"
            
            vrecon=[]
            lagcoef = []
            for counter in range(l):
                elementshares = []
                for vshare in shares:
                    elementshares.append(vshare[counter])
                if not lagcoef:
                    lagcoef = self._lagrange(elementshares, delta)
                vrecon.append(self._recon(elementshares,t, delta, lagcoef))
            return vrecon
        else:
            return self._recon(shares, t, delta)


    def _lagrange(self,shares,delta):
        k = len(shares)
        indices = []
        for x in shares:
            idx = x.idx
            if any(y == idx for y in indices):
                raise ValueError("Duplicate share")
            indices.append(idx)

        coefs = {}
        for j in range(k):
            x_j = indices[j]

            numerator = 1
            denominator = 1

            for m in range(k):
                x_m = indices[m]
                if m != j:
                    numerator *= x_m
                    denominator *=  x_m - x_j
            coefs[x_j] = (delta * numerator) // denominator
        return coefs
                    
    def _recon(self, shares, t, delta, lagcoefs=None):
        assert len(shares) >= t, "not enough shares, cannot reconstruct!" 
        raw_shares = []
        for x in shares:
            idx = x.idx
            value = x.value
            if any(y[0] == idx for y in raw_shares):
                raise ValueError("Duplicate share")
            raw_shares.append((idx, value))
        k = len(shares)
        result = 0
        if not lagcoefs:
            for j in range(k):
                x_j, y_j = raw_shares[j]

                numerator = 1
                denominator = 1

                for m in range(k):
                    x_m = raw_shares[m][0]
                    if m != j:
                        numerator *= x_m
                        denominator *= x_m - x_j
                r = (y_j * delta * numerator) // denominator
                result += r
            return result // (delta**2)
        else:
            for j in range(k):
                x_j, y_j = raw_shares[j]
                r = y_j * lagcoefs[x_j]
                result += r
            return result // delta**2
