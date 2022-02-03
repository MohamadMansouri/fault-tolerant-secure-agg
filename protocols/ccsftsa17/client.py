import random
from math import ceil, log2
from ecdsa import keys
from ecdsa.curves import SECP112r1
import gmpy2

from protocols.buildingblocks.utils import add_vectors, subs_vectors
from protocols.buildingblocks.PRG import PRG
from protocols.buildingblocks.ShamirSS import SSS, Share
from protocols.buildingblocks.KeyAggreement import KAS
from protocols.buildingblocks.AESGCM128 import EncryptionKey as AESKEY



class Client(object):
    dimension = 1000 # dimension of the input
    valuesize = 16 #-bit input values
    nclients = 10 # number of FL clients
    expandedvaluesize = valuesize + ceil(log2(nclients))
    keysize = 256 # size of a DH key 
    threshold = ceil(2*nclients / 3) # threshold for secret sharing
    Uall = [i+1 for i in range(nclients)] # set of all user identifiers

    # init the building blocks
    prg = PRG(dimension, valuesize)
    SSb = SSS(PRG.security) # t-out-of-n SS for the blinding mask b
    SSsk = SSS(keysize) # t-out-of-n SS for the deffie-hellman secret key
    KA = KAS()

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
        Client.KA = KAS()

    def new_fl_step(self):
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
        # generate DH key pairs for masking key
        self.KAs.generate()
                
        # generate DH key pairs for channel key
        self.KAc.generate()

        self.U1.append(self.user)

        # send user id and public keys
        return self.user, self.KAs.pk, self.KAc.pk

    def share_keys(self, alldhpks, alldhpkc):
        
        assert alldhpkc.keys() == alldhpks.keys()
        assert len(alldhpkc.keys()) >= self.threshold
        assert setlen(alldhpkc.values()) == len(alldhpkc.values())  
        assert setlen(alldhpks.values()) == len(alldhpks.values())  

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




def setlen(l):
    s = set()
    for e in l:
        k = repr(e)
        s.add(k)
    return len(s)