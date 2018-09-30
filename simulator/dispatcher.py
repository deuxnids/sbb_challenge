import random
import numpy as np


class Dispatcher(object):
    def __init__(self, sim):
        random.seed(20180101)
        self.sim = sim
        self.wait = False

    def choose(self, section):
        choices = []
        weights = []
        for s in section.choices.keys():
            choices.append(s)
            weights.append(section.choices[s])

        #return sections[-1]
        return np.random.choice(choices, p=np.array(weights)/sum(weights))


