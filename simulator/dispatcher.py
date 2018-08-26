import random


class Dispatcher(object):
    def __init__(self, sim):
        random.seed(20180101)
        self.sim = sim
        self.wait = False

    def choose(self, sections, train):
        #return sections[-1]
        return random.choice(sections)


