from collections import defaultdict
import random
import numpy as np
import logging


class QTable(object):
    def __init__(self):
        self.q_values = defaultdict(lambda: defaultdict(lambda: -9999999))

        self.epsilon = 0.1
        self.alpha = 0.1
        self.gamma = 0.6

        self.to_avoid = defaultdict(set)

    def get_action(self, choices, state):

        if random.uniform(0, 1) < self.epsilon or len(self.q_values[state].values()) == 0:
            action = random.choice(choices)  # Explore action space
        else:
            link_id_max = self.get_max(state)
            choices = {c.get_id(): c for c in choices}
            action = choices[link_id_max]
        return action

    def get_max(self, state):
        link_ids = list(self.q_values[state].keys())
        link_values = self.q_values[state].values()
        link_id = link_ids[np.argmax(link_values)]
        return link_id

    def update_table(self, previous_state, current_state, previous_action, reward):
        previous_value = self.q_values[previous_state][previous_action.get_id()]
        next_max = 0
        if len(self.q_values[current_state].values()) > 0:
            next_max = max(self.q_values[current_state].values())
        new_value = (1 - self.alpha) * previous_value + self.alpha * (reward + self.gamma * next_max)
        self.q_values[previous_state][previous_action.get_id()] = new_value


def get_state_id(train, trains):
    section_id = None
    try:
        section_id = train.solution.sections[-1]
    except:
        pass
    _hash = "%s_%s/" % (train.get_id(), section_id)
    for _train in trains:
        __hash = "/"
        try:
            __hash = _train.solution.sections[-1].get_id()
        except:
            pass
        _hash += "%s/" % __hash

    return _hash
