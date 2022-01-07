import time , csv, os


class Clock(object):
    LOGFILE = "time_measurements.csv"
    def __init__(self, phase, round, entity, scenario, ) -> None:
        super().__init__()
        self.phase = phase
        self.round = round
        self.entity = entity
        self.logfile, exist = self.openlogfile()
        self.csvwriter = csv.writer(self.logfile)
        self.start = None
        self.scenario = scenario
        self.paused = None
        if not exist:
            self.logheader()

    def openlogfile(self):
        exist = False
        if os.path.exists(Clock.LOGFILE):
            exist = True
        return open(Clock.LOGFILE, "a"), exist
    
    def logheader(self):
        l = self.scenario.header() + ["entity", "phase", "round", "time"]
        self.csvwriter.writerow(l)

    def logvalue(self, value):
        l = self.scenario.tolist() + [self.entity, self.phase, self.round, value]
        self.csvwriter.writerow(l)
        self.logfile.flush()

    def measure_from_here(self):
        assert self.paused is None
        self.start = time.perf_counter()

    def measure_pause(self):
        self.paused = time.perf_counter() - self.start

    def measure_continue(self):
        assert self.paused is not None
        self.start = time.perf_counter()

    def measure_till_here(self):
        t = time.perf_counter() - self.start
        if self.paused:
            t += self.paused
        self.start = None
        self.paused = None
        self.logvalue(t)    

    def finish(self):
        if not self.logfile.closed:
            self.logfile.close()
