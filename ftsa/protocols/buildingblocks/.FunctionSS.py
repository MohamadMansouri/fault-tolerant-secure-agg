from os import urandom as rng
from math import factorial

from ftsa.protocols.buildingblocks.ShamirSS import Share
from ftsa.protocols.buildingblocks.utils import powmod
from ftsa.protocols.buildingblocks.FullDomainHash import FDH
from ftsa.protocols.utils.CommMeasure import User

class FShare(Share):
    H = None
    mod = None
    bitlength = None
    nbitlength = None
    def __init__(self, idx, value=None) -> None:
        super().__init__(idx, value)
        self.mod = FShare.mod
        self.mod2 = self.mod * self.mod

    # def __initcopy__(self, share) -> None:
    #     super().__init__(share.idx, share.value)
    #     self.mod = FShare.mod
    #     self.mod2 = self.mod * self.mod
    
    def __add__(self, other):
        assert self.idx == other.idx, "Adding shares of different indexs"
        return FShare(self.idx, self.value + other.value)

    # def __mul__(self, other):
    #     assert self.idx == other.idx, "Multiplying shares of different indexs"
    #     return FShare(self.idx, (self.value * other.value) % self.mod2)

    def setup(mod, H, bitlength, nbitlength):
        FShare.mod = mod
        FShare.H = H
        FShare.bitlength = bitlength
        FShare.nbitlength = nbitlength
        
    def f(self, x):
        return FShare.f_raw(x, self.value, self.mod2)

    def f_raw(x, alpha,n2):
        # return FShare.Field(powmod(FShare.H(x)._value, alpha._value, n2._value))
        return powmod(FShare.H(x), alpha, n2)

    def eval(self,x):
        try: 
            y = self.f(x)
            return FShare(self.idx, y)
        except:
            raise ValueError("Shared function is not defined. (Please run setup for the class)")

    def eval_vector(self,x,vsize):
        try: 
            Y = []
            for i in range(vsize):
                y = self.f((i << FShare.nbitlength // 2) | x)
                Y.append(FShare(self.idx, y))
            return Y
        except:
            raise ValueError("Shared function is not defined. (Please run setup for the class)")
    
    def getrealsize(self):
        return User.size + self.bitlength 
    


class FSS(object):
    def __init__(self, bitlength, mod) -> None:
        super().__init__()
        self.bitlength = bitlength
        self.nbitlength = bitlength // 2
        self.mod = mod
        self.mod2 = mod*mod
        # def H(t):
        #     r = (powmod(t,self.mod,self.mod2)) % (self.mod2)
        #     return r
        FShare.setup(mod, FDH(self.bitlength, self.mod2).H, bitlength, self.nbitlength )



    def share(self,k,n,secret):

        coeffs = [int.from_bytes(rng(int(self.bitlength / 8)),"big") for i in range(k - 1)]
        coeffs.append(secret)

        # Each share is y_i = p(x_i) where x_i is the public index
        # associated to each of the n users.

        def make_share(idx, coeffs):
            share = 0
            for coeff in coeffs:
                share = idx * share + coeff
            return share
        return [FShare(i, make_share(i, coeffs)) for i in range(1, n + 1)]
    
    def lagrange(self,shares,delta):
        k = len(shares)
        gf_ind = []
        for x in shares:
            idx = x.idx
            if any(y == idx for y in gf_ind):
                raise ValueError("Duplicate share")
            gf_ind.append(idx)

        coefs = {}
        for j in range(k):
            x_j = gf_ind[j]

            numerator = 1
            denominator = 1

            for m in range(k):
                x_m = gf_ind[m]
                if m != j:
                    numerator *= x_m
                    denominator *=  x_m - x_j
            coefs[x_j] = (delta * numerator) // denominator
        return coefs
                    
    def recon(self, shares, delta, lagcoefs=None):
        gf_shares = []
        for x in shares:
            idx = x.idx
            value = x.value
            if any(y[0] == idx for y in gf_shares):
                raise ValueError("Duplicate share")
            gf_shares.append((idx, value))
        k = len(shares)
        result = 1
        if not lagcoefs:
            for j in range(k):
                x_j, y_j = gf_shares[j]

                numerator = 1
                denominator = 1

                for m in range(k):
                    x_m = gf_shares[m][0]
                    if m != j:
                        numerator *= x_m
                        denominator *= x_m - x_j
                r = powmod(y_j,(delta * numerator) // denominator,self.mod2)
                result = (result * r) % self.mod2
            return result
        else:
            if not isinstance(list(lagcoefs.keys())[0], int):
                lagcoefs = {x._value: y._value for x,y in lagcoefs.items()}
            for j in range(k):
                x_j, y_j = gf_shares[j]
                r = powmod(y_j,lagcoefs[x_j],self.mod2)
                result = (result * r) % self.mod2
            return result

    def recon_vector(self, vshares, delta, lagcoefs=None):
        assert len(vshares) > 0 , "empty list of shares to reconstruct from"
        l = len(vshares[0])
        for v in vshares:
            assert l == len(v), "attempting to reconstruct vectors of different size"
        
        reconv=[]
        lagcoef = []
        if lagcoefs: 
            lagcoef = lagcoefs
        for counter in range(l):
            shares = []
            for v in vshares:
                shares.append(v[counter])
            if not lagcoef:
                lagcoef = self.lagrange(shares, delta)
            reconv.append(self.recon(shares, delta, lagcoef))
        return reconv
        

    # def recon(self, shares, lagcoefs=None):
    #     gf_shares = []
    #     for x in shares:
    #         idx = self.Field(x.idx)
    #         value = x.value
    #         if any(y[0] == idx for y in gf_shares):
    #             raise ValueError("Duplicate share")
    #         gf_shares.append((idx, value))
    #     k = len(shares)
    #     result = self.Field(1)
    #     if not lagcoefs:
    #         for j in range(k):
    #             x_j, y_j = gf_shares[j]

    #             numerator = self.Field(1)
    #             denominator = self.Field(1)

    #             for m in range(k):
    #                 x_m = gf_shares[m][0]
    #                 if m != j:
    #                     numerator *= x_m
    #                     denominator *= x_m - x_j
    #             r = self.Field(powmod(y_j._value,(numerator * denominator.inverse())._value, self.mod2))
    #             result = (result * r) % self.mod2 
    #         return result._value
    #     else:
    #         for j in range(k):
    #             x_j, y_j = gf_shares[j]
    #             r = self.Field(powmod(y_j._value,lagcoefs[x_j]._value,self.mod2))
    #             result *= y_j ** lagcoefs[x_j]
    #         result %=  self.Field(self.mod2 )
    #         return result._value            
