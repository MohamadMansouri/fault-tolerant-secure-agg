"""
### **Joye-Libert secure aggregation scheme (JL) and its threshold-variant (TJL)**  

This module contains a python implementation of the Joye-Libert scheme and the threshold-variant of Joye-Libert scheme. The original scheme of Joye-Libert can be found here [1]. The threshold variant is defined here [2].

*Implemented by: Mohamad Mansouri (mohamad.mansouri@thalesgroup.com)*

[1] *Marc Joye and Benoît Libert. A scalable scheme for
privacy-preserving aggregation of time-series data. In
Ahmad-Reza Sadeghi, editor, Financial Cryptography
and Data Security. Springer Berlin Heidelberg, 2013.*

[2] *publication in progress*

"""

from math import factorial
import random
from gmpy2 import mpz

from ftsa.protocols.buildingblocks.utils import getprimeover, invert, powmod
from ftsa.protocols.buildingblocks.FullDomainHash import FDH
from ftsa.protocols.buildingblocks.IntegerSS import ISSS, IShare


DEFAULT_KEY_SIZE = 2048

class JLS(object):
    """
    The Joye-Libert scheme. It consists of three Probabilistic Polynomial Time algorithms: **Setup**, 
    **Protect**, and **Agg**.

    ## **Args**:
    -------------        
    *nusers* : `int` --
        The number of users in the scheme

    *VE* : `VectorEncoding` --
        The vector encoding/decoding scheme (default: `None`)

    ## **Attributes**:
    -------------        
    *nusers* : `int` --
        The number of users in the scheme

    *VE* : `VectorEncoding` --
        The vector encoding/decoding scheme

    *keysize* : `int` --
        The bit length of the keys
    

    
    """
    def __init__(self, nusers, VE=None):
        super().__init__()
        self.nusers = nusers
        self.keysize = None
        self.VE = VE

    def Setup(self, lmbda=DEFAULT_KEY_SIZE):
        """
        Setups the users and the server with the secret keys and public parameters

        ### Given some security parameter \\(\\lambda\\), this algorithm generates two equal-size prime numbers \\(p\\) and \\(q\\) and sets \\(N = pq\\). It randomly generates \\(n\\) secret keys \\(sk_u \\xleftarrow{R} \\pm \\{0,1\\}^{2l}\\) where \\(l\\) is the number of bits of \\(N\\) and sets \\(sk_0 = -\\sum_{1}^n{sk_u}\\). Then, it defines a cryptographic hash function \\(H : \\mathbb{Z} \\rightarrow \\mathbb{Z}_{N^2}^{*}\\). It outputs the \\(n+1\\) keys and the public parameters \\((N, H)\\). 

        ## **Args**:
        -------------        
        **lmbda** : `int` --
            The bit length the user/server key 

        ## **Returns**:
        -------------
        The public parameters, server key, a list of user keys:  `(PublicParam, ServerKey, list[UserKeys])`
        """
        self.keysize = lmbda

        p = q = n = None
        n_len = 0
        while n_len != lmbda // 2:
            p = getprimeover(lmbda // 4)
            q = p
            while q == p:
                q = getprimeover(lmbda // 4)
            n = p * q
            n_len = n.bit_length()

        fdh = FDH(self.keysize, n*n)


        public_param = PublicParam(n, lmbda // 2, fdh.H)
        
        seed = random.SystemRandom()
        s0 = mpz(0)
        users = {}
        
        for i in range(self.nusers):
            s = mpz(seed.getrandbits(2*n_len))
            users[i] = UserKey(public_param, s)
            s0+=s
        s0 = -s0
        server = ServerKey(public_param, s0)


        return public_param, server, users


    def Protect(self, pp, sk_u, tau, x_u_tau):
        """
        Protect user input with the user's secret key: \\(y_{u,\\tau} \\gets \\textbf{JL.Protect}(pp,sk_u,\\tau,x_{u,\\tau})\\)

        ### This algorithm encrypts private inputs \\(x_{u,\\tau} \\in \\mathbb{Z}_N\\) for time period \\(\\tau\\) using secret key \\(sk_u \\in \\mathbb{Z}_N^2\\) . It outputs cipher \\(y_{u,\\tau}\\) such that:
        
        $$y_{u,\\tau} = (1 + x_{u,\\tau} N) H(\\tau)^{sk_u} \\mod N^2$$
        
        ## **Args**:
        -------------

        *pp* : `PublicParam` --
            The public parameters \\(pp\\)

        *sk_u* : `UserKey` --
            The user's secret key \\(sk_u\\)

        *tau* : `int` --
            The time period \\(\\tau\\)

        *x_u_tau* : `int` or `list` --
            The user's input \\(x_{u,\\tau}\\)

        ## **Returns**:
        -------------
        The protected input of type `EncryptedNumber` or a list of `EncryptedNumber`
        """
        assert isinstance(sk_u, UserKey), "bad user key"
        assert sk_u.pp == pp, "bad user key"

        if isinstance(x_u_tau, list):
            x_u_tau = self.VE.encode(x_u_tau)
            return sk_u.encrypt(x_u_tau, tau)
        else: 
            return sk_u.encrypt(x_u_tau, tau)

    def Agg(self,pp, sk_0, tau,list_y_u_tau):
        """
        Aggregate users protected inputs with the server's secret key: \\(X_{\\tau} \\gets \\textbf{JL.Agg}(pp, sk_0,\\tau, \\{y_{u,\\tau}\\}_{u \\in \\{1,..,n\\}})\\)

        ### This algorithm aggregates the \\(n\\) ciphers received at time period \\(\\tau\\) to obtain \\(y_{\\tau} = \\prod_1^n{y_{u,\\tau}}\\) and decrypts the result. It obtains the sum of the private inputs ( \\( X_{\\tau} = \\sum_{1}^n{x_{u,\\tau}} \\) ) as follows:
        
        $$V_{\\tau} = H(\\tau)^{sk_0} \\cdot y_{\\tau} \\qquad \\qquad X_{\\tau} = \\frac{V_{\\tau}-1}{N} \\mod N$$
        
        ## **Args**:
        -------------

        *pp* : `PublicParam` --
            The public parameters \\(pp\\)

        *sk_0* : `ServerKey` --
            The server's secret key \\(sk_0\\)

        *tau* : `int` --
            The time period \\(\\tau\\)

        *list_y_u_tau* : `list` --
            A list of the users' protected inputs \\(\\{y_{u,\\tau}\\}_{u \\in \\{1,..,n\\}}\\)

        ## **Returns**:
        -------------
        The sum of the users' inputs of type `int` 
        """

        assert isinstance(sk_0, ServerKey), "bad server key"
        assert sk_0.pp == pp, "bad server key"
        assert isinstance(list_y_u_tau, list), "list_y_u_tau should be a list"
        assert len(list_y_u_tau) > 0 , "list_y_u_tau should contain at least one protected input"
        if isinstance(list_y_u_tau[0], list):
            for y_u_tau in list_y_u_tau:
                assert len(list_y_u_tau[0]) == len(y_u_tau), "attempting to aggregate protected vectors of different sizes"
            y_tau=[]
            for i in range(len(list_y_u_tau[0])):
                y_tau_i = list_y_u_tau[0][i]
                for y_u_tau in list_y_u_tau[1:]:
                    y_tau_i += y_u_tau[i]
                y_tau.append(y_tau_i)
            d = sk_0.decrypt(y_tau, tau)
            sum_x_u_tau = self.VE.decode(d)

        else: 
            assert isinstance(list_y_u_tau[0], EncryptedNumber), "bad ciphertext"
            y_tau = list_y_u_tau[0]
            for y_u_tau in list_y_u_tau[1:]:
                y_tau += y_u_tau
            sum_x_u_tau = sk_0.decrypt(y_tau, tau)

        return sum_x_u_tau

class TJLS(JLS):
    """
    The Threshold version of Joye-Libert scheme. It consists of six Probabilistic Polynomial Time algorithms: **Setup**, **SKShare**, **ShareProtect**, **ShareCombine**, **Protect**, and **Agg**.

    ## **Args**:
    -------------        
    *nusers* : `int` --
        The number of users in the scheme

    *threshold* : `int` --
        The secret sharing reconstruction threshold 

    *VE* : `VectorEncoding` --
        The vector encoding/decoding scheme

    *sigma* : `int`
        The security parameter \\(sigma\\) for **ISS** (default: 128)

    ## **Attributes**:
    -------------        
    *threshold* : `int` --
        The secret sharing reconstruction threshold 

    *delta* : `int`
        The factorial of number of users

    *sigma* : `int`
        The security parameter \\(sigma\\) for **ISS** (default: 128)

    *ISS* : `ISSS`
        The integer sharing scheme


    """
    def __init__(self, nusers, threshold, VE=None, sigma=128):
        super().__init__(nusers, VE)
        self.threshold = threshold
        self.delta = factorial(self.nusers)
        self.sigma = sigma
        self.ISS = None

    def Setup(self, lmbda=DEFAULT_KEY_SIZE):
        """
        This calls the **JL.Setup(lmbda)** method. It additionally initializes the **ISS** scheme. 
        """

        public_param, server, users =  super().Setup(lmbda)
        self.ISS = ISSS(self.keysize, self.sigma)
        return public_param, server, users

    def SKShare(self, sk_u, t, U):
        """
        Share the secret sk_u with all users in U: 
        $$\\{(v,[\\Delta sk_u]_v)\\}_{\\forall v \\in \\mathcal{U}} \\gets \\textbf{TJL.SKShare}(sk_u,t,\\mathcal{U})$$

        ### On input of user \\(u\\)'s secret key, this algorithm calls \\(\\textbf{ISS.Share}(sk_u,t,\\mathcal{U})\\) where the interval of the secret \\(sk_u\\) is \\([-2^{2l},2^{2l}]\\) and \\(l\\) is the number of bits of the modulus \\(N\\). It constructs a secret sharing of the private key \\(sk_u\\) over the integers. Hence, this algorithm outputs \\(n\\) shares of user \\(u\\)'s key \\(sk_u\\), each share \\([\\Delta sk_u]_v\\) is for each user \\(v \\in \\mathcal{U}\\).

        ## **Args**:
        -------------
        *sk_u* : `UserKey` --
            The secret key of user u
        
        *t* : `int` --
            The threshold of the secret sharing scheme

        *U* : `list` --
            The list of user identifier [1,...,n]
        
        ## **Returns**:
        ----------------
        A list of shares of the secret key. Each share is of type `IShare`
        """
        return self.ISS.Share(sk_u.s, t, U)
        
    
    def ShareProtect(self, pp, list_sk_v_ushare, tau):
        """
        Protect a zero value with u's shares of all failed users' secret keys: 
        $$[ y'_{\\tau}]_u \\gets \\textbf{TJL.ShareProtect}(pp,\\{[\\Delta sk_v]_u\\}_{v\\in \\mathcal{U}''},\\tau)$$

        ### This algorithm protects a zero-value with user \\(u\\)s shares of all the secret keys corresponding to the failed users ( \\(v \\in\\mathcal{U}''\\) ) ( \\([\\Delta sk_v]_u\\) is the user \\(u\\) share of the secret key \\(sk_v\\) corresponding to the failed user \\(v\\) ). It basically calls \\(\\textbf{JL.Protect}(pp,\\sum_{v\\in \\mathcal{U}''}[\\Delta sk_v]_u,\\tau, 0)\\) and outputs \\([y'_{\\tau}]_u = H(\\tau)^{\\sum_{v\\in \\mathcal{U}''}[\\Delta sk_v]_u} \\mod N^2\\). This algorithm is called when there are failed users and hence their input need to be recovered.

        ## **Args**:
        -------------
        *pp* : `PublicParam` --
            The public parameters \\(pp\\)

        *list_sk_v_ushare* : `list` --
            A list of shares of all failed users' secret keys

        *tau* : `int` --
            The time period \\(\\tau\\)

        
        ## **Returns**:
        ----------------
        A share of the protected zero-value with all failed users keys of type `IntSecretShare`
        """
        sharesum = list_sk_v_ushare[0]
        idx = sharesum.idx
        for share in list_sk_v_ushare[1:]:
            sharesum += share
        keyshare = UserKey(pp, sharesum.value) 
        if self.VE is not None:
            yzero_ushare_tau =  self.Protect(pp, keyshare, tau, [0] * self.VE.vectorsize)
            IShare.bits = yzero_ushare_tau[0].ciphertext.bit_length()
            r = []
            for yzero_ushare_tau_i in yzero_ushare_tau: 
                r.append(IShare(idx,yzero_ushare_tau_i))
            return r
        else:
            yzero_ushare_tau = self.Protect(pp, keyshare, tau, 0)
            return IShare(idx, yzero_ushare_tau)
    
    def ShareCombine(self, pp, list_yzero_ushare_tau, t):
        """
        Combine the shares of all protected zero-value: 
        $$y'_{\\tau} \\gets \\textbf{TJL.ShareCombine}(pp, \\{(u,[y'_{\\tau}]_u, n)\\}_{\\forall u \\in \\mathcal{U}'},t)$$

        ### This algorithm combines \\(t\\) out of \\(n\\) protected shares of the zero-value for time step \\(\\tau\\) and given \\(\\Delta = n!\\). \\(\\mathcal{U}'\\) is a subset of the online users such that \\(|\\mathcal{U}'| \\geq t\\) and \\(\\mathcal{U}''\\) is the set of failed users. It computes the Lagrange interpolation on the exponent.

        ## **Args**:
        -------------
        *pp* : `PublicParam` --
            The public parameters \\(pp\\)

        *list_yzero_ushare_tau* : `list` --
            A list of shares of the protected zero-value of all failed users
        
        *t* : `int` --
            The threshold of the secret sharing scheme

        *lagcoef*: `list` -- 
            The lagrange coeficients

        ## **Returns**:
        ----------------
        The protected zero-value of all failed users at time period tau. Value of type `gmpy.mpz` or `list`
        """
        assert len(list_yzero_ushare_tau) > 0 , "empty list of shares to reconstruct from"

        def _recon(shares, t, delta, lagcoefs=None): 
            assert len(shares) >= t, "not enough shares, cannot reconstruct!" 
            raw_shares = []
            for x in shares:
                idx = x.idx
                value = x.value
                if any(y[0] == idx for y in raw_shares):
                    raise ValueError("Duplicate share")
                raw_shares.append((idx, value))
            k = len(shares)
            result = 1
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
                    r = powmod(y_j.ciphertext,(delta * numerator) // denominator, pp.nsquare)
                    result = (result * r) % pp.nsquare
                return EncryptedNumber(pp,result)
            else:
                for j in range(k):
                    x_j, y_j = raw_shares[j]
                    r = powmod(y_j.ciphertext,lagcoefs[x_j],pp.nsquare)
                    result = (result * r) % pp.nsquare
                return EncryptedNumber(pp,result)
        
        if isinstance(list_yzero_ushare_tau[0], list):
            l = len(list_yzero_ushare_tau[0])
            for vshare in list_yzero_ushare_tau:
                assert l == len(vshare), "shares of the vector does not have the same size"
            
            vrecon=[]
            lagcoef = []
            for counter in range(l):
                elementshares = []
                for vshare in list_yzero_ushare_tau:
                    elementshares.append(vshare[counter])
                if not lagcoef:
                    lagcoef = self.ISS._lagrange(elementshares, self.delta)
                vrecon.append(_recon(elementshares,t, self.delta, lagcoef))
            return vrecon
        else:
            return _recon(list_yzero_ushare_tau, t, self.delta)
        


    def Agg(self,pp, sk_0, tau,list_y_u_tau, yzero_tau=None):
        """
        Aggregate users protected inputs with the server's secret key: 
        $$X_{\\tau} \\gets \\textbf{TJL.Agg}(pp, sk_0,\\tau, \\{y_{u,\\tau}\\}_{\\forall u \\in \\mathcal{U}'},y'_\\tau)$$

        ### On input the public parameters \\(pp\\), the aggregation key \\(sk_0\\), the individual ciphertexts of online users ( \\(u \\in \\mathcal{U}'\\)), and the ciphertexts of the zero-value corresponding to the failed users, this algorithm aggregates the ciphers of time period \\(\\tau\\) by first multiplying the inputs for all online users, raising them to the power \\({\\Delta^2}\\), and multiplying the result with the ciphertext of the zero-value. \\(\\mathcal{U}'\\) is that set of online users and \\(\\mathcal{U}'' = \\mathcal{U} \\setminus \\mathcal{U}'\\) is the set of failed users. It computes:
        
        $$y'_{\\tau} = (\\prod\\limits_{\\forall u \\in \\mathcal{U}'}{y_{u,\\tau}})^{\\Delta^2} \\cdot y'_\\tau \\mod N^2 =(1+{\\Delta^2} \\sum\\limits_{\\forall u \\in \\mathcal{U}'}x_{u,\\tau} N)H(\\tau)^{{\\Delta^2} \\sum\\limits_{\\forall u \\in \\mathcal{U}'}sk_u} \\cdot H(\\tau)^{{\\Delta^2} \\sum\\limits_{\\forall u \\in \\mathcal{U}''}sk_u} $$
        $$= (1+{\\Delta^2} \\sum\\limits_{\\forall u \\in \\mathcal{U}'}x_{u,\\tau} N)H(\\tau)^{{\\Delta^2} \\sum\\limits_{\\forall u \\in \\mathcal{U}}sk_u}$$

        ### To decrypt the final result, the algorithm proceeds as follows:  
        $$ V_{\\tau} = H(\\tau)^{ {\\Delta^2} sk_0} \\cdot y'_{\\tau}  \\qquad \\qquad X_{\\tau} = \\frac{V_{\\tau}-1}{N{\\Delta^2} } \\mod N$$


        
        ## **Args**:
        -------------
        *pp* : `PublicParam` --
            The public parameters \\(pp\\)

        *sk_0* : `ServerKey` --
            The server's secret key \\(sk_0\\)

        *tau* : `int` --
            The time period \\(\\tau\\)

        *list_y_u_tau* : `list` --
            A list of the users' protected inputs \\(\\{y_{u,\\tau}\\}_{u \\in \\{1,..,n\\}}\\)

        ## **Returns**:
        -------------
        The sum of the users' inputs of type `int` 
        """
        assert isinstance(sk_0, ServerKey), "bad server key"
        assert sk_0.pp == pp, "bad server key"
        assert isinstance(list_y_u_tau, list), "list_y_u_tau should be a list"
        assert len(list_y_u_tau) > 0 , "list_y_u_tau should contain at least one protected input"
        if not yzero_tau: assert(len(list_y_u_tau) == self.nusers), "missing user inputs and no protected zero-value"
        if isinstance(list_y_u_tau[0], list):
            if yzero_tau: assert len(list_y_u_tau[0]) == len(yzero_tau), "bad vector length"
            for y_u_tau in list_y_u_tau:
                assert len(y_u_tau) == len(list_y_u_tau[0]), "bad vector length"
            y_tau=[]
            delta = 1
            for i in range(len(list_y_u_tau[0])):
                y_tau_i = list_y_u_tau[0][i]
                for y_u_tau in list_y_u_tau[1:]:
                    y_tau_i += y_u_tau[i]
                if len(list_y_u_tau) != self.nusers:
                    y_tau_i = EncryptedNumber(pp,powmod(y_tau_i.ciphertext, self.delta**2, sk_0.pp.nsquare))
                    y_tau_i +=  yzero_tau[i]
                    delta = self.delta
                y_tau.append(y_tau_i)

            d = sk_0.decrypt(y_tau, tau, delta)
            sum_x_u_tau = self.VE.decode(d)

        else: 
            assert isinstance(list_y_u_tau[0], EncryptedNumber), "bad ciphertext"
            y_tau = list_y_u_tau[0]
            delta = 1
            for y_u_tau in list_y_u_tau[1:]:
                y_tau += y_u_tau
            if len(list_y_u_tau) != self.nusers:
                y_tau = EncryptedNumber(pp,powmod(y_tau.ciphertext, self.delta**2, sk_0.pp.nsquare))
                y_tau += yzero_tau
                delta = self.delta
            sum_x_u_tau = sk_0.decrypt(y_tau, tau, delta)

        return sum_x_u_tau

class PublicParam(object):
    """
    The public parameters for Joye-Libert Scheme.

    ## **Args**:
    -------------
    **n** : `gmpy2.mpz` --
        The modulus \\(N\\)

    **bits** : `int` --
        The number of bits of the modulus \\(N\\)

    **H** : `function` --
        The hash algorithm \\(H : \\mathbb{Z} \\rightarrow \\mathbb{Z}_{N^2}^{*}\\)


    ## **Attributes**:
    -------------
    **n** : `gmpy2.mpz` --
        The modulus \\(N\\)

    **nsquare** : `gmpy2.mpz` --
        The square of the modulus \\(N^2\\)        

    **bits** : `int` --
        The number of bits of the modulus \\(N\\)

    **H** : `function` --
        The hash algorithm \\(H : \\mathbb{Z} \\rightarrow \\mathbb{Z}_{N^2}^{*}\\)
    """
    def __init__(self, n, bits, H):
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

class UserKey(object):
    """
    A user key for Joye-Libert Scheme.

    ## **Args**:
    -------------
    **param** : `PublicParam` --
        The public parameters

    **key** : `gmpy2.mpz` --
        The value of the user's key \\(sk_0\\)

    ## **Attributes**:
    -------------
    **param** : `PublicParam` --
        The public parameters

    **key** : `gmpy2.mpz` --
        The value of the user's key \\(sk_0\\)
    """

    def __init__(self, param, key):
        super().__init__()
        self.pp = param
        self.s = key


    def __repr__(self):
        hashcode = hex(hash(self))
        return "<UserKey {}>".format(hashcode[:10])

    def __eq__(self, other):
        return (self.pp == other.pp and self.s == other.s )

    def __hash__(self):
        return hash(self.s)

    def encrypt(self, plaintext, tau):
        """
        Encrypts a plaintext  for time period tau  
    
        ## **Args**:
        -------------
        **plaintext** : `int` or `gmpy2.mpz` --
            the plaintext to encrypt 

        **tau** : `int` --
            the time period 

        ## **Returns**:
        ---------------
        A ciphertext of the *plaintext* encrypted by the user key of type `EncryptedNumber`
        """
        if isinstance(plaintext, list):
            counter = 0
            cipher = []
            for pt in plaintext:
                cipher.append(self._encrypt(pt, (counter << self.pp.bits // 2) | tau))
                counter += 1
        else: 
            cipher = self._encrypt(plaintext, tau)
        return cipher

    def _encrypt(self, plaintext, tau):
        nude_ciphertext = (self.pp.n * plaintext + 1) % self.pp.nsquare
        r = powmod(self.pp.H(tau), self.s, self.pp.nsquare)
        ciphertext = (nude_ciphertext * r) % self.pp.nsquare
        return EncryptedNumber(self.pp, ciphertext)

class ServerKey(object):
    """
    A server key for Joye-Libert Scheme.

    ## **Args**:
    -------------
    **param** : `PublicParam` --
        The public parameters

    **key** : `gmpy2.mpz` --
        The value of the server's key \\(sk_0\\)

    ## **Attributes**:
    -------------
    **param** : `PublicParam` --
        The public parameters

    **key** : `gmpy2.mpz` --
        The value of the server's key \\(sk_0\\)
    """
    
    def __init__(self, param, key):
        super().__init__()
        self.pp = param
        self.s = key

    def __repr__(self):
        hashcode = hex(hash(self))
        return "<ServerKey {}>".format(hashcode[:10])

    def __eq__(self, other):
        return (self.pp == other.pp and self.s == other.s )

    def __hash__(self):
        return hash(self.s)

    def decrypt(self, cipher, tau, delta=1):
        """
        Decrypts the aggregated ciphertexts of all users for time period tau  
    
        ## **Args**:
        -------------
        **cipher** : `EncryptedNumber` --
            An aggregated ciphertext 

        **tau** : `int` --
            the time period 

        ## **Returns**:
        ---------------
        The sum of user inputs of type `int`
        """
    
        if isinstance(cipher, list):
            counter = 0
            pt = []
            for c in cipher:
                pt.append(self._decrypt(c, (counter << self.pp.bits // 2) | tau, delta))
                counter +=1
        else: 
            pt = self._decrypt(cipher, tau, delta)
        return pt
    
    def _decrypt(self, cipher, tau, delta=1):
        if not isinstance(cipher, EncryptedNumber):
            raise TypeError('Expected encrypted number type but got: %s' %
                            type(cipher))
        if self.pp != cipher.pp:
            raise ValueError('encrypted_number was encrypted against a '
                             'different key!')
        return self._raw_decrypt(cipher.ciphertext, tau, delta)
    

    def _raw_decrypt(self, ciphertext, tau, delta=1):
        if not isinstance(ciphertext, mpz):
            raise TypeError('Expected mpz type ciphertext but got: %s' %
                        type(ciphertext))
        V = (ciphertext * powmod(self.pp.H(tau), delta**2 * self.s, self.pp.nsquare)) % self.pp.nsquare
        X = ((V - 1) // self.pp.n)  % self.pp.n
        X = (X * invert(delta**2, self.pp.nsquare)) % self.pp.n
        return int(X)
    

class EncryptedNumber(object):
    """
    An encrypted number by one of the user keys .

    ## **Args**:
    -------------
    **param** : `PublicParam` --
        The public parameters

    **ciphertext** : `gmpy2.mpz` --
        The integer value of the ciphertext

    ## **Attributes**:
    -------------
    **param** : `PublicParam` --
        The public parameters

    **ciphertext** : `gmpy2.mpz` --
        The integer value of the ciphertext
    """
    def __init__(self, param, ciphertext):
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
        """
        returns the size of the ciphertext
        """
        return self.pp.bits*2
