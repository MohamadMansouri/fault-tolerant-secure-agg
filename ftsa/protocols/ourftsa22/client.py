import random
from math import ceil
import gmpy2

from ftsa.protocols.buildingblocks.utils import add_vectors
from ftsa.protocols.buildingblocks.PRG import PRG
from ftsa.protocols.buildingblocks.ShamirSS import SSS, Share
from ftsa.protocols.buildingblocks.IntegerSS import IShare
from ftsa.protocols.buildingblocks.JoyeLibert import TJLS, UserKey
from ftsa.protocols.buildingblocks.VectorEncoding import VES
from ftsa.protocols.buildingblocks.KeyAggreement import KAS
from ftsa.protocols.buildingblocks.AESGCM128 import EncryptionKey as AESKEY



class Client(object):
    """
    A client for the FTSA scheme

    ## **Args**:
    -------------        
    *user* : `int` --
        The user's id

    ## **Attributes**:
    -------------        
    *user* : `int` --
        The user's id

    *step* : `int` --
        The FL step (round).

    *key* : `gmpy2.mpz` --
        The user protection key for TJL

    *ckeys* : `dict` --
        A channel encryption key for each communication channel with each other user {v : key}

    *U* : `list` --
        Set of registered user identifiers

    *Ualive* : `list` --
        Set of alive users' identifiers 

    *bshares* : `dict` --
        A share of the b value of each other user {v : bshare}

    *keyshares* : `dict` --
        A share of the key of each other user {v : keyshare}

    *X* : `list` --
        The user input vector

    *KAs*  : `KAS` --
        DH KA scheme for computing JL key

    *KAc*  : `KAS` --
        DH KA scheme for computing channel key
    """
    dimension = 1000 # dimension of the input
    """nb. of elements of the input vector (default: 1000)"""
    valuesize = 16 #-bit input values
    """bit length of each element in the input vector (default: 16)"""
    nclients = 10 # number of FL clients
    """number of FL clients (default: 10)"""
    keysize = 2048 # size of a JL key 
    """size of a TJL key (default: 2048)"""
    threshold = ceil(2*nclients / 3) # threshold for secret sharing
    """threshold for secret sharing scheme (default: 2/3 of the nb. of clients)"""
    Uall = [i+1 for i in range(nclients)] # set of all user identifiers
    """set of all user identifiers"""

    # init the building blocks
    VE = VES(keysize // 2, nclients, valuesize, dimension)
    """the vector encoding scheme"""
    TJL = TJLS(nclients, threshold, VE)
    """the threshold JL secure aggregation scheme"""
    pp, _ , _ = TJL.Setup(keysize) # public parameters for TJL
    """the public parameters"""
    prg = PRG(dimension, valuesize)
    """the pseudo-random generator"""
    SS = SSS(PRG.security)
    """the secret sharing scheme"""

    def __init__(self, user) -> None:
        super().__init__()
        self.user = user # the user identifier (we use values in [1,nclients])
        self.step = 0 # the Fl step.
        self.key = gmpy2.mpz(0) # the user encryption key for JL
        self.ckeys = {} # a channel encryption key for each communication channel with each other user {v : key}
        self.U = [] # set of registered user identifiers
        self.Ualive = [] # set of alive users' identifiers 
        self.bshares = {} # a share of the b value of each other user {v : bshare}
        self.keyshares = {} # a share of the key of each other user {v : keyshare}
        self.X = [] # the user input vector
        self.KAs= KAS() # DH KA scheme for computing JL key
        self.KAc= KAS() # DH KA scheme for computing channel key

    @staticmethod
    def set_scenario(dimension, valuesize, keysize, threshold, nclients, publicparam):
        """Sets up the parameters of the protocol."""
        Client.dimension = dimension
        Client.valuesize = valuesize
        Client.nclients = nclients
        Client.keysize = keysize
        Client.threshold = threshold
        Client.Uall = [i+1 for i in range(nclients)]
        Client.VE = VES(keysize // 2, nclients, valuesize, dimension)
        Client.TJL = TJLS(nclients,threshold, Client.VE)
        Client.TJL.Setup(keysize) 
        Client.pp = publicparam
        Client.prg = PRG(dimension, valuesize)
        Client.SS = SSS(PRG.security)

    def new_fl_step(self):
        """Starts a new FL round. 
        
        It increments the round counter and regenrates a new random input (This should be replaced with the actual training of the model)."""
        self.step += 1
        self.Ualive = []
        self.bshares = {}
        # generate a new input vector
        self.X = [random.SystemRandom().getrandbits(Client.valuesize) for _ in range(Client.dimension)]
                
    def setup_register(self):
        """Setup phase - Register: User registers to te server. 
        
        It generates public keys.
        
        **Returns**: 
        ----------------
        A user identifier, and two public keys (type: (`int`, `PublicKey`, `PublicKey`)).
        """
        # generate DH key pairs for JL key
        self.KAs.generate()
                
        # generate DH key pairs for channel key
        self.KAc.generate()

        self.U.append(self.user)

        # send user id and public keys
        return self.user, self.KAs.pk, self.KAc.pk

    def setup_keysetup(self, alldhpks, alldhpkc):
        """Setup phase - KeySetup: User setups its keys. 
        
        It accepts the public keys of other users and computes the shared keys and the JL key. It also shares the JL key using **TJL.SKShare** and returns its shares.
        
        ** Args **:
        -----------
        *alldhpkc* : `dict` -- 
            The public key of each user (used to construct secret channels).

        *alldhpks* : `dict` -- 
            The public key of each user (used to compute the TJL user keys).

        **Returns**: 
        ----------------
        The user identifier and a dictionary of encrypted shares of its TJL secret key (type: (`int`, `dict`)).
        """
        assert alldhpkc.keys() == alldhpks.keys()
        assert len(alldhpkc.keys()) >= self.threshold
        assert _setlen(alldhpkc.values()) == len(alldhpkc.values())  
        assert _setlen(alldhpks.values()) == len(alldhpks.values())  

        # for each user compute agreed key
        for vuser in alldhpkc:
            if vuser == self.user:
                continue
            
            self.U.append(vuser)

            # compute channel key
            self.ckeys[vuser] = self.KAc.agree(alldhpkc[vuser])
            
            # compute JL key
            sv = self.KAs.agree(alldhpks[vuser], Client.keysize)
            if vuser > self.user:
                self.key -= sv
            else:
                self.key += sv

        self.key = UserKey(Client.pp, self.key)

        # generate t-out-of-n shares of JL key
        shares = Client.TJL.SKShare(self.key, self.threshold, self.U)
        
        # encrypt the shares for each user
        E = {}
        for share in shares:
            vuser = share.idx
            if self.user == vuser:
                self.keyshares[self.user] = share
                continue
            key = AESKEY(self.ckeys[vuser])
            message = self.user.to_bytes(2,"big") + vuser.to_bytes(2,"big") + gmpy2.to_binary(share.value)
            e = key.encrypt(message)
            E[vuser] = e
        
        # send the user id and the encrypted shares
        return self.user, E

    def setup_keysetup2(self, eshares):
        """Setup phase - KeySetup: User setups its keys. 
        
        It completes the setup phase by receiving the shares of the JL keys of all other users and storing them.
        
        ** Args **:
        -----------
        *eshares* : `dict` -- 
            The shares of the JL keys.
        """
        assert len(eshares) + 1 >= self.threshold
    
        # set the registered users and decrypt the shares
        for vuser in eshares: 
            key = AESKEY(self.ckeys[vuser])
            message = key.decrypt(eshares[vuser])
            u = int.from_bytes(message[:2],"big")
            v = int.from_bytes(message[2:4],"big")
            assert v == self.user and u == vuser, "invalid encrypted message" 
            share = gmpy2.from_binary(message[4:])
            self.keyshares[vuser] = IShare(self.user, share)
        return 

    def online_encrypt(self):
        """Online phase - Encrypt: User protect its input and sends it to the server. 
        
        It protects the user input using **TJL.Protect** and a random generated mask. It returns the protected input and the shares of the mask seed
        
        **Returns**: 
        ----------------
        The user identifier, a dictionary of encryptes shares of its mask seed, and the protected input (type: (`int`, `dict`, `list`)."""

        # sample a random element b
        b = random.SystemRandom().getrandbits(PRG.security)

        # extend b using PRG
        B = Client.prg.eval(b)

        # encrypt the message
        XplusB = add_vectors(self.X,B,2**(Client.VE.elementsize))
        Y = Client.TJL.Protect(Client.pp, self.key, self.step, XplusB)

        # generate t-out-of-U shares of b
        shares = Client.SS.share(self.threshold, self.nclients, b)

        # encrypt the shares for each user
        E = {}

        for share in shares:
            vuser = share.idx
            if self.user == vuser:
                self.bshares[self.user] = share
                continue
            key = AESKEY(self.ckeys[vuser])
            message = self.user.to_bytes(2,"big") + vuser.to_bytes(2,"big") + gmpy2.to_binary(share.value._value)
            e = key.encrypt(message)
            E[vuser] = e

        # send user id, encrypted shares, and the encrypted input
        return self.user, E, Y

    def online_construct(self, eshares):
        """Online phase - Construct: User send the shares of the users to the server.

        It receives the shares of other users and deduce the alive users. For all not alive user, it computes the protected zero-value using **TJL.ShareProtect**. It returns the shares of the blinding mask seed of alive users and a share of the protected zero-value.

        ** Args **:
        -----------
        *eshares* : `dict` -- 
            The encrypted shares of the blinding mask of each alive user

        **Returns**: 
        ----------------
        The user identifier, the shares of the blinding mask seed of alive users, and a share of the protected zero-value (type: (`int`, `dict`, `list`)).
        """
        assert len(eshares) + 1 >= self.threshold

        self.Ualive = [self.user]
        # deduce the alive users and decrypt the shares
        for vuser in eshares: 
            self.Ualive.append(vuser)
            key = AESKEY(self.ckeys[vuser])
            message = key.decrypt(eshares[vuser])
            u = int.from_bytes(message[:2],"big")
            v = int.from_bytes(message[2:4],"big")
            share = gmpy2.from_binary(message[4:])
            assert v == self.user and u == vuser, "invalid encrypted message"
            self.bshares[vuser] = Share(self.user, Client.SS.Field(share))


        # compute the shares of the missing component Ybar
        dropshares = []
        Yzeroshare = None
        if self.U != self.Ualive:
            for vuser in self.U:
                if vuser in self.Ualive:
                    continue
                dropshares.append(self.keyshares[vuser])
            if dropshares:
                Yzeroshare = Client.TJL.ShareProtect(Client.pp, dropshares, self.step)

        # send the secret shares and the missing component
        return self.user, self.bshares, Yzeroshare


def _setlen(l):
    s = set()
    for e in l:
        k = repr(e)
        s.add(k)
    return len(s)