import random
from math import ceil, log2
from ecdsa import keys
from ecdsa.curves import SECP112r1
import gmpy2

from ftsa.protocols.buildingblocks.utils import add_vectors, subs_vectors
from ftsa.protocols.buildingblocks.PRG import PRG
from ftsa.protocols.buildingblocks.ShamirSS import SSS, Share
from ftsa.protocols.buildingblocks.KeyAggreement import KAS
from ftsa.protocols.buildingblocks.AESGCM128 import EncryptionKey as AESKEY



class Client(object):
    """
    A client for the FTSA scheme proposed by Google team in CCS17

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

    *key* : `list` --
        The user's mask

    *ckeys* : `dict` --
        A channel encryption key for each communication channel with each other user {v : key}

    *U1* : `list` --
        Set of round 1 users' identifiers

    *U2* : `list` --
        Set of round 2 users' identifiers

    *U4* : `list` --
        Set of round 4 users' identifiers

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

    *b* : `int` --
        The blinding mask seed
    
    *alldhpks* : `dict` -- 
        The public key of each user (used to compute the user's mask).
    """

    dimension = 1000 # dimension of the input
    """nb. of elements of the input vector (default: 1000)"""
    valuesize = 16 #-bit input values
    """bit length of each element in the input vector (default: 16)"""
    nclients = 10 # number of FL clients
    """number of FL clients (default: 10)"""
    expandedvaluesize = valuesize + ceil(log2(nclients))
    """The expanded bit length to hold the sum of inputs"""
    keysize = 256 # size of a DH key 
    """size of a DH key (default: 256)"""
    threshold = ceil(2*nclients / 3) # threshold for secret sharing
    """threshold for secret sharing scheme (default: 2/3 of the nb. of clients)"""
    Uall = [i+1 for i in range(nclients)] # set of all user identifiers
    """set of all user identifiers"""

    # init the building blocks
    prg = PRG(dimension, valuesize)
    """the pseudo-random generator"""
    SSb = SSS(PRG.security) # t-out-of-n SS for the blinding mask b
    """the secret sharing scheme for sharing the blinding mask"""
    SSsk = SSS(keysize) # t-out-of-n SS for the deffie-hellman secret key
    """the secret sharing scheme for sharing the user mask"""


    def __init__(self, user) -> None:
        super().__init__()
        self.user = user # the user identifier (we use values in [1,nclients])
        self.step = 1 # the Fl step.
        self.key = [0]*Client.dimension # the user masking key 
        self.ckeys = {} # a channel encryption key for each communication channel with each other user {v : key}
        self.U1 = [] # set of round 1 users
        self.U2 = [] # set of round 2 users
        self.U4 = [] # set of round 4 users
        self.bshares = {} # a share of the b value of each other user {v : bshare}
        self.keyshares = {} # a share of the key of each other user {v : keyshare}
        self.X = [] # the user input vector
        self.KAs= KAS() # DH KA scheme for computing masking key
        self.KAc= KAS() # DH KA scheme for computing channel key
        self.b = 0 # blinding mask
        self.alldhpks = {} # received DH public keys 

    @staticmethod
    def set_scenario(dimension, valuesize, keysize, threshold, nclients):
        """Sets up the parameters of the protocol."""
        Client.dimension = dimension
        Client.valuesize = valuesize
        Client.nclients = nclients
        Client.expandedvaluesize = valuesize + ceil(log2(nclients))
        Client.keysize = keysize
        Client.threshold = threshold
        Client.Uall = [i+1 for i in range(nclients)]
        Client.prg = PRG(dimension, valuesize)
        Client.SSb = SSS(PRG.security)
        Client.SSsk = SSS(keysize)

    def new_fl_step(self):
        """Starts a new FL round. 
        
        It increments the round counter and regenrates a new random input (This should be replaced with the actual training of the model)."""   
        self.step += 1
        self.U1 = []
        self.U2 = []
        self.U4 = []
        self.bshares = {}
        self.keyshares = {}
        self.bshares = {}
        self.KAs= KAS() 
        self.KAc= KAS() 
        self.ckeys = {}
        self.b = 0
        self.alldhpks = {}
        self.key = [0]*Client.dimension
        # generate a new input vector
        self.X = [random.SystemRandom().getrandbits(Client.valuesize) for _ in range(Client.dimension)]
                
    def advertise_keys(self):
        """Round 0 - AdvertiseKeys: User advertise the his generated keys. 
        
        **Returns**: 
        ----------------
        A user identifier, and two public keys (type: (`int`, `PublicKey`, `PublicKey`)).
        """

        # generate DH key pairs for masking key
        self.KAs.generate()
                
        # generate DH key pairs for channel key
        self.KAc.generate()

        self.U1.append(self.user)

        # send user id and public keys
        return self.user, self.KAs.pk, self.KAc.pk

    def share_keys(self, alldhpks, alldhpkc):
        """Round 1 - ShareKeys: User setups and share its keys with other users. 
        
        It accepts the public keys of other users and computes the shared keys and the JL key. It also shares the JL key using **TJL.SKShare** and returns its shares.
        
        ** Args **:
        -----------
        *alldhpkc* : `dict` -- 
            The public key of each user (used to construct secret channels).

        *alldhpks* : `dict` -- 
            The public key of each user (used to compute the user mask).

        **Returns**: 
        ----------------
        The user identifier and a dictionary of encrypted share pairs of the blinding mask and DH secret key  (type: (`int`, `dict`)).
        """
        assert alldhpkc.keys() == alldhpks.keys()
        assert len(alldhpkc.keys()) >= self.threshold
        assert _setlen(alldhpkc.values()) == len(alldhpkc.values())  
        assert _setlen(alldhpks.values()) == len(alldhpks.values())  

        self.U1 += list(alldhpks.keys())

        # for each user compute agreed key
        for vuser in alldhpkc:
            if vuser == self.user:
                continue
            # compute channel key
            self.ckeys[vuser] = self.KAc.agree(alldhpkc[vuser])


        # sample a random element b
        self.b = random.SystemRandom().getrandbits(128)

        # generate t-out-of-U shares of b
        bshares = Client.SSb.share(self.threshold, self.nclients, self.b)


        # generate t-out-of-n shares of DH key
        kshares = Client.SSsk.share(self.threshold, self.nclients, self.KAs.get_sk_bytes())

        # encrypt the shares for each user
        E = {}
        for kshare, bshare in zip(kshares, bshares):
            assert kshare.idx == bshare.idx
            vuser = kshare.idx
            if self.user == vuser:
                self.keyshares[self.user] = kshare
                self.bshares[self.user] = bshare
                continue
            key = AESKEY(self.ckeys[vuser])
            sharelen = len(gmpy2.to_binary(kshare.value._value))
            message = self.user.to_bytes(2,"big") + vuser.to_bytes(2,"big") + sharelen.to_bytes(2,"big") + gmpy2.to_binary(kshare.value._value) + gmpy2.to_binary(bshare.value._value)
            e = key.encrypt(message)
            E[vuser] = e

        self.alldhpks = alldhpks
     
        # send the user id and the encrypted shares
        return self.user, E

    def masked_input_collection(self, eshares):
        """Round 2 - MaskedInputCollection: User protect its input and sends it to the server. 
        
        ## **Args**:
        -------------
        *eshares* : `dict` -- 
            The encrypted shares of the blinding mask and the Dh key of the users

        **Returns**: 
        ----------------
        The user identifier, and the protected input (type: (`int`, `list`)."""
        assert len(eshares) + 1 >= self.threshold

        self.U2 = [self.user] + list(eshares.keys())
        self.eshares = eshares

        # for each user compute masking agreed key
        for vuser in self.alldhpks:
            if vuser == self.user:
                continue
            # compute masking key
            sv = self.KAs.agree(self.alldhpks[vuser])
            if vuser > self.user:
                self.key = subs_vectors(self.key, Client.prg.eval(sv), 2**Client.expandedvaluesize)
            else:
                self.key = add_vectors(self.key, Client.prg.eval(sv), 2**Client.expandedvaluesize)
        
        # extend b using PRG
        B = Client.prg.eval(self.b)

        # compute the masked input
        mask = add_vectors(self.key, B, 2**Client.expandedvaluesize)
        Y = add_vectors(self.X, mask, 2**Client.expandedvaluesize)

        return self.user, Y

    def unmasking(self, U4):
        """Round 4 - UnMasking: User send the shares of the users to the server.

        ** Args **:
        -----------
        *U4* : `list` -- 
            The list of still alive users

        **Returns**: 
        ----------------
        The user identifier, the shares of the DH secret key for dead users, and the shares of the blinding mask seed of alive users (type: (`int`, `dict`, `dict`)).
        """
        assert len(U4) >= self.threshold
        assert set(U4).issubset(set(self.U2))

        self.U4 = U4

        # decrypt the shares
        for vuser in self.eshares: 
            key = AESKEY(self.ckeys[vuser])
            message = key.decrypt(self.eshares[vuser])
            u = int.from_bytes(message[:2],"big")
            v = int.from_bytes(message[2:4],"big")
            sharelen = int.from_bytes(message[4:6],"big")
            assert v == self.user and u == vuser, "invalid encrypted message"
            kshare = gmpy2.from_binary(message[6:sharelen+6])
            bshare = gmpy2.from_binary(message[sharelen+6:])
            self.bshares[vuser] = Share(self.user, Client.SSb.Field(bshare))
            self.keyshares[vuser] = Share(self.user, Client.SSsk.Field(kshare))


        # send either the b share of the key share of each user
        bshares = {}
        kshares = {}
        for vuser in self.U2:
            if vuser in self.U4:
                bshares[vuser] = self.bshares[vuser]
            else:
                kshares[vuser] = self.keyshares[vuser]


        # send the secret shares of b and key
        return self.user, kshares, bshares




def _setlen(l):
    s = set()
    for e in l:
        k = repr(e)
        s.add(k)
    return len(s)