from collections import defaultdict
import random
import numpy as np
import logging


class QTable(object):
    def __init__(self):
        self.q_values = defaultdict(lambda: defaultdict(lambda: 0))

        self.epsilon = 0.9
        self.alpha = 0.1
        self.gamma = 0.6

        self.to_avoid = defaultdict(list)

    def remove(self, state, action):
        if state in self.q_values:
            if action in self.q_values[state]:
                del self.q_values[state]

    def get_action(self, choices, state):
        if len(choices) == 1:
            return choices[0]

        if random.uniform(0, 1) < self.epsilon:
            action = random.choice(choices)  # Explore action space
        else:
            max_value = -999999
            action = None
            for c in choices:
                value = self.q_values[state][c.get_id()]
                if value > max_value:
                    action = c
                    max_value = value
        return action

    def update_table(self, previous_state, current_state, previous_action, reward):
        previous_value = self.q_values[previous_state][previous_action.get_id()]
        next_max = 0
        if len(self.q_values[current_state].values()) > 0:
            next_max = max(self.q_values[current_state].values())
        new_value = (1 - self.alpha) * previous_value + self.alpha * (reward + self.gamma * next_max)
        self.q_values[previous_state][previous_action.get_id()] = new_value

    def do_not_go(self, on, if_on):
        #if on not in self.to_avoid:
        #    return False

        if if_on in self.to_avoid[on]:
            logging.info("%s should already by avoided" % on)
            return

        self.to_avoid[on].append(if_on)

    def can_go(self, on, if_are_on):
        if on not in self.to_avoid:
            return True

        for if_is_on in if_are_on:
            if if_is_on in self.to_avoid[on]:
                return False

        return True


def get_state_id(train, limit):
    return "ass"
    n = len(train.solution.sections)
    if n == 0:
        return "start_%s" % train
    else:
        s = train.solution.sections[-1]
    flat_list = list(set([item for sublist in train.compute_routes(s.get_end_node(), limit=limit) for item in sublist]))
    flat_list = sorted(flat_list, key=lambda x: x.get_id())

    _id = "%s_%s->" % (train, s.get_id())

    for item in flat_list:
        ids = list(set(map(str, item.block_by())))
        if len(ids) > 0:
            _id += "%s[" % item.get_id() + "-".join(ids) + "]"

    return _id
