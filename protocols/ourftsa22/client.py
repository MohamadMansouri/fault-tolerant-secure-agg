import random
from math import ceil
import gmpy2

from protocols.buildingblocks.utils import add_vectors
from protocols.buildingblocks.PRG import PRG
from protocols.buildingblocks.ShamirSS import SSS, Share
from protocols.buildingblocks.FunctionSS import FSS, FShare
from protocols.buildingblocks.JoyeLibert import JLS, UserKey
from protocols.buildingblocks.KeyAggreement import KAS
from protocols.buildingblocks.AESGCM128 import EncryptionKey as AESKEY



class Client(object):
    dimension = 1000 # dimension of the input
    valuesize = 16 #-bit input values
    nclients = 10 # number of FL clients
    keysize = 2048 # size of a JL key 
    threshold = ceil(2*nclients / 3) # threshold for secret sharing
    Uall = [i+1 for i in range(nclients)] # set of all user identifiers

    # init the building blocks
    JL = JLS(nclients, valuesize, dimension, keysize)
    publicparam, _ , _ = JL.generate_keys() # public parameters for JL and for the FSS
    prg = PRG(dimension, valuesize)
    SS = SSS(PRG.security)
    FS = FSS(keysize, publicparam.n)

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
        Client.dimension = dimension
        Client.valuesize = valuesize
        Client.nclients = nclients
        Client.keysize = keysize
        Client.threshold = threshold
        Client.Uall = [i+1 for i in range(nclients)]
        Client.JL = JLS(nclients, valuesize, dimension, keysize)
        Client.publicparam = publicparam
        Client.prg = PRG(dimension, valuesize)
        Client.SS = SSS(PRG.security)
        Client.FS = FSS(keysize, Client.publicparam.n)

    def new_fl_step(self):
        self.step += 1
        self.Ualive = []
        self.bshares = {}
        # generate a new input vector
        self.X = [random.SystemRandom().getrandbits(Client.valuesize) for _ in range(Client.dimension)]
                
    def setup_register(self):
        # generate DH key pairs for JL key
        self.KAs.generate()
                
        # generate DH key pairs for channel key
        self.KAc.generate()

        self.U.append(self.user)

        # send user id and public keys
        return self.user, self.KAs.pk, self.KAc.pk

    def setup_keysetup(self, alldhpks, alldhpkc):
        
        assert alldhpkc.keys() == alldhpks.keys()
        assert len(alldhpkc.keys()) >= self.threshold
        assert setlen(alldhpkc.values()) == len(alldhpkc.values())  
        assert setlen(alldhpks.values()) == len(alldhpks.values())  

        # for each user compute agreed key
        for vuser in alldhpkc:
            if vuser == self.user:
                continue
            
            # compute channel key
            self.ckeys[vuser] = self.KAc.agree(alldhpkc[vuser])
            
            # compute JL key
            sv = self.KAs.agree(alldhpks[vuser], Client.keysize)
            if vuser > self.user:
                self.key -= sv
            else:
                self.key += sv

        self.key = UserKey(self.user, Client.publicparam, self.key, Client.JL.VE)

        # generate t-out-of-n shares of JL key
        shares = Client.FS.share(self.threshold, self.nclients, self.key.s)
        
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

        assert len(eshares) + 1 >= self.threshold
    
        # set the registered users and decrypt the shares
        for vuser in eshares: 
            self.U.append(vuser)
            key = AESKEY(self.ckeys[vuser])
            message = key.decrypt(eshares[vuser])
            u = int.from_bytes(message[:2],"big")
            v = int.from_bytes(message[2:4],"big")
            assert v == self.user and u == vuser, "invalid encrypted message" 
            share = gmpy2.from_binary(message[4:])
            self.keyshares[vuser] = FShare(self.user, share)
        return 

    def online_encrypt(self):
        # sample a random element b
        b = random.SystemRandom().getrandbits(PRG.security)

        # extend b using PRG
        B = Client.prg.eval(b)

        # encrypt the message
        XplusB = add_vectors(self.X,B,2**(Client.JL.VE.elementsize))
        Y = self.key.encrypt_vector(XplusB, self.step)

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
        fshare = FShare(self.user, 0)
        Ybarshare = None
        if self.U != self.Ualive:
            for vuser in self.U:
                if vuser in self.Ualive:
                    continue
                fshare += self.keyshares[vuser]
            Ybarshare = fshare.eval_vector(self.step, Client.JL.VE.numbatches)

        # send the secret shares and the missing component
        return self.user, self.bshares, Ybarshare


def setlen(l):
    s = set()
    for e in l:
        k = repr(e)
        s.add(k)
    return len(s)