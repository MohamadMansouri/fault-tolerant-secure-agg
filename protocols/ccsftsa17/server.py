from collections import defaultdict
from math import ceil, log2

from protocols.buildingblocks.utils import subs_vectors, add_vectors
from protocols.buildingblocks.PRG import PRG
from protocols.buildingblocks.ShamirSS import SSS
from protocols.buildingblocks.KeyAggreement import KAS



class Server(object):
    dimension = 1000 # dimension of the input
    valuesize = 16 #-bit input values
    nclients = 10 # number of FL clients
    expandedvaluesize = valuesize + ceil(log2(nclients))
    keysize = 256 # size of a DH key 
    threshold = ceil(2*nclients / 3) # threshold for secret sharing

    # init the building blocks
    prg = PRG(dimension, valuesize)
    SSb = SSS(prg.security) # SS scheme for the blinding mask b
    SSsk = SSS(keysize) # SS scheme for the DH key

    def __init__(self) -> None:
        super().__init__()
        self.step = 1 # the Fl step.
        self.U1 = [] # set of round 1 users
        self.U2 = [] # set of round 2 users
        self.U3 = [] # set of round 3 users
        self.U5 = [] # set of round 4 users
        self.alldhpks = {} # received DH public keys 
        self.allY = {} # all masked inputs

    @staticmethod
    def set_scenario(dimension, valuesize, keysize, threshold, nclients):
        Server.dimension = dimension
        Server.valuesize = valuesize
        Server.nclients = nclients
        Server.expandedvaluesize = valuesize + ceil(log2(nclients))
        Server.keysize = keysize
        Server.threshold = threshold
        Server.prg = PRG(dimension, valuesize)
        Server.SSb = SSS(Server.prg.security)
        Server.SSsk = SSS(keysize)

    def new_fl_step(self):
        self.step += 1
        self.U1 = []
        self.U2 = []
        self.U3 = []
        self.U5 = []
        self.allY = {} 
    
    def advertise_keys(self, alldhpks, alldhpkc):

        self.U1 = list(alldhpkc.keys())

        assert alldhpkc.keys() == alldhpks.keys()
        assert len(self.U1) >= Server.threshold

        self.alldhpks = alldhpks

        # send for all user public keys
        return alldhpks, alldhpkc

    def share_keys(self, allekshares):

        self.U2 = list(allekshares.keys())

        assert len(self.U2) >= Server.threshold


        # prepare eshares for each corresponding user
        ekshares = defaultdict(dict)
        for user in allekshares:
            for vuser in allekshares[user]:
                ekshares[vuser][user] = allekshares[user][vuser]
        
        # send the encrypted key shares for each corresponding user
        return ekshares

    def masked_input_collection(self, allY):

        self.U3 = list(allY.keys())
        
        assert len(self.U3) >= Server.threshold
        assert set(self.U3).issubset(set(self.U2))

        self.allY = allY

        # assert len(allebshares) >= Server.threshold

        # # prepare eshares for each corresponding user
        # ebshares = defaultdict(dict)
        # for user in allebshares:
        #     self.Ualive.append(user)
        #     for vuser in allebshares[user]:
        #         ebshares[vuser][user] = allebshares[user][vuser]

        # # aggregate all encrypted messages
        # Ytelda = Server.JL.aggregate_vector(list(allY.values()))
        # self.Ytelda = Ytelda
        # # self.Ytelda = [powmod(x.ciphertext, factorial(Server.nclients), Server.publicparam.nsquare) for x in Ytelda]

        # send the encrypted b shares for each corresponding user
        return self.U3 

    def unmasking(self, allkshares, allbshares):
        
        self.U5 = list(allbshares.keys())

        assert len(self.U5) >= Server.threshold


        # reconstruct the blinding mask seed b for each alive user 
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
                lagcoef = Server.SSb.lagrange(bshares[vuser])
            b[vuser] = Server.SSb.recon(bshares[vuser],lagcoef)
            # recompute the blinding vector B
            B[vuser] = Server.prg.eval(b[vuser])


        # reconstruct the dh key for each dead user 
        kshares = defaultdict(list)
        for user in allkshares:
            for vuser in allkshares[user]:
                kshares[vuser].append(allkshares[user][vuser])
        dhkey = {}
        lagcoef = []
        for vuser in kshares:
            assert len(kshares[vuser]) >= Server.threshold
            if not lagcoef:
                lagcoef = Server.SSsk.lagrange(kshares[vuser])
            k = Server.SSsk.recon(kshares[vuser],lagcoef)
            k = int(k)
            dhkey[vuser] = KAS().generate_from_bytes(k.to_bytes((k.bit_length() + 7) // 8, "big"))

        # recompute their masking agreed keys 
        skey = {}
        for user in self.U2:
            if user in self.U3:
                continue
            key = [0] * Server.dimension
            for vuser in self.alldhpks:
                if vuser == user:
                    continue
                sv = dhkey[user].agree(self.alldhpks[vuser])
                if vuser > user:
                    key = subs_vectors(key, Server.prg.eval(sv), 2**Server.expandedvaluesize)
                else:
                    key = add_vectors(key, Server.prg.eval(sv), 2**Server.expandedvaluesize)
            
            skey[user] = key

        # decrypt the masks
        result = [0] * Server.dimension
        for user in self.allY:
            result = add_vectors(result, self.allY[user], 2**Server.expandedvaluesize) 
        for user in skey:
            result = add_vectors(result, skey[user], 2**Server.expandedvaluesize) 
        for user in B:
            result = subs_vectors(result, B[user], 2**Server.expandedvaluesize) 
        
        return result
