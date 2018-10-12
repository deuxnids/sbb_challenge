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
        link_values = list(self.q_values[state].values())
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
    limit = 12
    n = len(train.solution.sections)
    if n==0:
        return "start_%s" % train
    else:
        s = train.solution.sections[-1]
    flat_list = list(set([item for sublist in train.compute_routes(s.end_node, limit=limit) for item in sublist]))
    flat_list = sorted(flat_list, key=lambda x: x.get_id())

    _id = "%s_%s->" % (train, s.get_id())

    for item in flat_list:
        ids = list(set(map(str, item.block_by())))
        if len(ids)>0:
            _id += "%s[" % item.get_id() + "-".join(ids) + "]"
    return _id

