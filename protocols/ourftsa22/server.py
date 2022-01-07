from collections import defaultdict
from math import ceil, factorial
from gmpy2 import mpz

from protocols.buildingblocks.utils import subs_vectors, powmod
from protocols.buildingblocks.PRG import PRG
from protocols.buildingblocks.ShamirSS import SSS
from protocols.buildingblocks.FunctionSS import FSS
from protocols.buildingblocks.JoyeLibert import JLS, ServerKey, EncryptedNumber
from protocols.buildingblocks.KeyAggreement import KAS



class Server(object):
    dimension = 1000 # dimension of the input
    valuesize = 16 #-bit input values
    nclients = 10 # number of FL clients
    keysize = 2048 # size of a JL key 
    threshold = ceil(2*nclients / 3) # threshold for secret sharing

    # init the building blocks
    JL = JLS(nclients, valuesize, dimension, keysize)
    publicparam, _ , _ = JL.generate_keys() # public parameters for JL and for the FSS
    prg = PRG(dimension, valuesize)
    SS = SSS(PRG.security)
    FS = FSS(keysize, publicparam.n)
    KA = KAS()

    def __init__(self) -> None:
        super().__init__()
        self.step = 0 # the Fl step.
        self.key = ServerKey(Server.publicparam, mpz(0) , Server.JL.VE) # the server encryption key for JL (we use zero)
        self.U = [] # set of registered user identifiers
        self.Ualive = [] # set of alive users' identifiers 
        self.Ytelda = None # aggregation result of the users' ciphertext
        self.delta = 1
    @staticmethod
    def set_scenario(dimension, valuesize, keysize, threshold, nclients, publicparam):
        Server.dimension = dimension
        Server.valuesize = valuesize
        Server.nclients = nclients
        Server.keysize = keysize
        Server.threshold = threshold
        Server.JL = JLS(nclients, valuesize, dimension, keysize)
        Server.publicparam = publicparam
        Server.prg = PRG(dimension, valuesize)
        Server.SS = SSS(PRG.security)
        Server.FS = FSS(keysize, Server.publicparam.n)
        Server.KA = KAS()

    def new_fl_step(self):
        self.step += 1
        self.Ualive = []
        self.Ytelda = None
        self.delta = 1

    def setup_register(self, alldhpkc, alldhpks):

        assert alldhpkc.keys() == alldhpks.keys()
        assert len(alldhpkc.keys()) >= Server.threshold

        # send for all user public keys
        return alldhpkc, alldhpks

    def setup_keysetup(self, allekshares):

        assert len(allekshares) >= Server.threshold

        # prepare eshares for each corresponding user
        ekshares = defaultdict(dict)
        for user in allekshares:
            self.U.append(user)
            for vuser in allekshares[user]:
                ekshares[vuser][user] = allekshares[user][vuser]
        
        self.delta = factorial(len(self.U))

        # send the encrypted key shares for each corresponding user
        return ekshares

    def online_encrypt(self, allebshares, allY):

        assert len(allebshares) >= Server.threshold

        # prepare eshares for each corresponding user
        ebshares = defaultdict(dict)
        for user in allebshares:
            self.Ualive.append(user)
            for vuser in allebshares[user]:
                ebshares[vuser][user] = allebshares[user][vuser]

        # aggregate all encrypted messages
        self.Ytelda = Server.JL.aggregate_vector(list(allY.values()))
        if len(allY) < len(self.U):
            self.Ytelda = [ EncryptedNumber( Server.publicparam, powmod(x.ciphertext, self.delta, Server.publicparam.nsquare)) for x in self.Ytelda]

        # send the encrypted b shares for each corresponding user
        return ebshares 

    def online_construct(self, allbshares, Ybarshares = None):
        
        assert len(allbshares) >= Server.threshold

        # reconstruct the blinding mask seed b for each user 
        bshares = defaultdict(list)
        for user in allbshares:
            for vuser in allbshares[user]:
                bshares[vuser].append(allbshares[user][vuser])

        lagcoef = []
        b = {}
        B = defaultdict(list)
        for vuser in bshares:
            assert len(bshares[vuser]) >= Server.threshold
            if not lagcoef:
                lagcoef = Server.SS.lagrange(bshares[vuser])
            b[vuser] = Server.SS.recon(bshares[vuser],lagcoef)
            # recompute the blinding vector B
            B[vuser] = Server.prg.eval(b[vuser])

        Y = self.Ytelda
        

        if Ybarshares:
            assert len(Ybarshares) >= Server.threshold
         
            # construct the missing component Ybar
            Ybar = Server.FS.recon_vector(list(Ybarshares.values()), self.delta)

            # aggregate the missing component
            Y = Server.JL.aggregate_vector([self.Ytelda, Ybar])

            # decrypt
            XplusB = self.key.decrypt_vector(Y, self.step, self.delta)
        
        else:
            # decrypt
            XplusB = self.key.decrypt_vector(Y, self.step)
        
        # unmask
        for user in B:
            XplusB = subs_vectors(XplusB, B[user], 2**(Server.JL.VE.elementsize))
        
        return XplusB
