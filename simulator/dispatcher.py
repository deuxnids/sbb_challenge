import random


class Dispatcher(object):
    def __init__(self):
        random.seed(20180101)

    def choose(self, sections):
        return random.choice(sections)


