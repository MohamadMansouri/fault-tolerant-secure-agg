"""
### **Shamir's Secret Sharing Scheme **

This module contains an implementation of Shamir's secret sharing (t-out-of-n) over a field of user choice.
"""
from os import urandom as rng

from ftsa.protocols.buildingblocks.utils import P64Field, P128Field, P256Field, P512Field, P1024Field, P2048Field
from ftsa.protocols.utils.CommMeasure import User


class Share(object):
    """A share of a secret value
    
    ## **Args**:
    -------------
    *idx* : `int` --
        the user index who holds the share

    *value* : `Field` --
        the raw value of the share

    ## **Attributes**:
    -------------
    *idx* : `int` --
        the user index who holds the share

    *value* : `Field` --
        the raw value of the share
    """
    def __init__(self, idx, value) -> None:
        super().__init__()
        self.idx = idx
        self.value = value
    def __add__(self, other):
        assert self.idx == other.idx, "Adding shares of different indexs"
        return Share(self.idx, self.value + other.value)

    def getrealsize(self):
        """returns the size of the share in bits"""
        return User.size + self.value.bits

class SSS(object):
    """The secret sharing scheme
    
    ## **Args**:
    -------------
    *bitlength* : `int` --
        the bit length of secrets to be shared

    ## **Attributes**:
    -------------
    *bitlength* : `int` --
        the bit length of secrets to be shared

    *Field* : `Field` --
        The field to be used for the operations
    
    """
    def __init__(self, bitlength) -> None:
        super().__init__()
        if bitlength <= 64:
            P64Field.bits = bitlength
            self.Field = P64Field
        elif bitlength <= 128:
            P128Field.bits = bitlength
            self.Field = P128Field
        elif bitlength <= 256:
            P256Field.bits = bitlength
            self.Field = P256Field
        elif bitlength <= 512:
            P512Field.bits = bitlength
            self.Field = P512Field
        elif bitlength <= 1024:
            P1024Field.bits = bitlength
            self.Field = P1024Field
        elif bitlength <= 2048:
            P2048Field.bits = bitlength
            self.Field = P2048Field                                    
        else: 
            raise ValueError("No sufficient field for this secret size")
        self.bitlength = bitlength

    def lagrange(self,shares):
        """computes the lagrange coefetions. It returns a dictionary of user indices as keys and lagrange coeficients as values"""
        k = len(shares)

        gf_ind = []
        for x in shares:
            idx = self.Field(x.idx)
            if any(y == idx for y in gf_ind):
                raise ValueError("Duplicate share")
            gf_ind.append(idx)

        coefs = {}
        for j in range(k):
            x_j = gf_ind[j]

            numerator = self.Field(1)
            denominator = self.Field(1)

            for m in range(k):
                x_m = gf_ind[m]
                if m != j:
                    numerator *= x_m
                    denominator *=  x_m - x_j
            coefs[x_j] = numerator * denominator.inverse()
        return coefs
                    
    def share(self,k, n, secret):
        """Shares a secret with n users with a threshold k. Returns a list of `Share` elements"""
        coeffs = [self.Field(rng(self.bitlength//8)) for i in range(k - 1)]
        coeffs.append(self.Field(secret))

        # Each share is y_i = p(x_i) where x_i is the public index
        # associated to each of the n users.

        def make_share(user, coeffs):
            idx = self.Field(user)
            share = self.Field(0)
            for coeff in coeffs:
                share = idx * share + coeff
            return share
        return [Share(i, make_share(i, coeffs)) for i in range(1, n + 1)]

    def recon(self,shares, lagcoefs=None):
        """Reconstructs a secret from a list of shares. If lagcoefs are not provided, it computes them. Returns the secret as an integer"""

        gf_shares = []
        for x in shares:
            idx = self.Field(x.idx)
            value = x.value
            if any(y[0] == idx for y in gf_shares):
                raise ValueError("Duplicate share")
            gf_shares.append((idx, value))
        k = len(shares)
        result = self.Field(0)
        if not lagcoefs:
            for j in range(k):
                x_j, y_j = gf_shares[j]

                numerator = self.Field(1)
                denominator = self.Field(1)

                for m in range(k):
                    x_m = gf_shares[m][0]
                    if m != j:
                        numerator *= x_m
                        denominator *= x_m - x_j
                result += y_j * numerator * denominator.inverse()
            return result._value
        else: 
            for j in range(k):
                x_j, y_j = gf_shares[j]
                result += y_j * lagcoefs[x_j]
            return result._value