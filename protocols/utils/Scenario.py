


class Scenario(object):
    def __init__(self,dimension=None,inputsize=None,
    keysize=None,threshold=None,nclients=None,dropout=None) -> None:
        super().__init__()
        self.dimension = dimension
        self.inputsize = inputsize
        self.keysize = keysize
        self.threshold = threshold
        self.nclients = nclients
        self.dropout = dropout
    
    def __hash__(self) -> int:
        return str(self.tolist()).__hash__()
    
    def __eq__(self, __o: object) -> bool:
        return \
        self.dimension == __o.dimension and \
        self.inputsize == __o.inputsize and \
        self.keysize == __o.keysize and\
        self.threshold == __o.threshold and\
        self.nclients == __o.nclients and\
        self.dropout == __o.dropout 

    def fromlist(self, l):
        self.__init__(*l)

    def fromdict(self, d):
        self.dimension = d["dimension"]
        self.inputsize = d["inputsize"]
        self.keysize = d["keysize"]
        self.threshold = d["threshold"]
        self.nclients = d["nclients"]
        self.dropout = d["dropout"]

    def todict(self):
        return {
        "dimension" : self.dimension,
        "inputsize" : self.inputsize,
        "keysize" : self.keysize,
        "threshold" : self.threshold,
        "nclients" : self.nclients,
        "dropout" : self.dropout
        }
    
    def tolist(self):
        return [
            self.dimension,
            self.inputsize,
            self.keysize,
            self.threshold,
            self.nclients,
            self.dropout
        ]
    
    def header(self):
        return list(self.todict().keys())
    