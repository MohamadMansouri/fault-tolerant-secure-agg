from ecdsa.keys import VerifyingKey
import csv, os

STRSIZE = 8
BYTSIZE = 8


class Bandwidth(object):
    LOGFILE = "comm_measurements.csv"
    def __init__(self, phase, round, scenario) -> None:
        super().__init__()
        self.phase = phase
        self.round = round
        self.logfile, exist = self.openlogfile()
        self.csvwriter = csv.writer(self.logfile)
        self.scenario = scenario
        if not exist:
            self.logheader()

    def openlogfile(self):
        exist = False
        if os.path.exists(Bandwidth.LOGFILE):
            exist = True
        return open(Bandwidth.LOGFILE, "a"), exist
    
    def logheader(self):
        l = self.scenario.header() + ["phase", "round", "direction", "size"]
        self.csvwriter.writerow(l)

    def logvalue(self, direction, value):
        l = self.scenario.tolist() + [self.phase, self.round, direction, value]
        self.csvwriter.writerow(l)
        self.logfile.flush()

    def measure_sent_data(self, data=None, hint=None):
        if not data:
            return
        self.logvalue("sent", getrealsize(data, hint))

    def measure_rcvd_data(self, data=None, hint=None):
        if not data:
            return
        self.logvalue("rcvd", getrealsize(data, hint)) 

    def finish(self):
        if not self.logfile.closed:
            self.logfile.close()



class User(object):
    size = 16 
    def __init__(self, user) -> None:
        super().__init__()
        self.user = user

def getrealsize(obj, hint=None):
    if not obj:
        return 0
    if isinstance(obj, int):
        if not hint:
            raise ValueError("int size cannot be specified automatically. Please give a hint")
        elif isinstance(hint, int):
            return hint
        else:
            return hint[0]
    elif isinstance(obj, str):
        return len(obj)*STRSIZE
    elif isinstance(obj, bytes):
        return len(obj)*BYTSIZE
    elif isinstance(obj, User):
        return User.size
    elif isinstance(obj,VerifyingKey):
        return getrealsize(obj.to_string(), hint)
    elif isinstance(obj, list):
        h = hint
        if isinstance(hint, list):
            h = hint[1]
        return sum([getrealsize(x,h) for x in obj])
    elif isinstance(obj, dict):
        return sum([getrealsize(x,hint) + getrealsize(y,hint)  for x,y in obj.items()])
    elif isinstance(obj, set):
        return sum([getrealsize(x,hint) for x in obj])
    elif isinstance(obj, tuple):
        return sum([getrealsize(x,hint) for x in obj])
    elif hasattr(obj, 'getrealsize'):
        return obj.getrealsize()
    else:
        raise ValueError("Type {} is of unkown real size!".format(type(obj)))


