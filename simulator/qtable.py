from collections import defaultdict
import random
import numpy as np
import logging


class QTable(object):
    def __init__(self):
        self.q_values = defaultdict(lambda: defaultdict(lambda: 0))

        self.epsilon = 0.1
        self.alpha = 0.1
        self.gamma = 0.6

    def get_action(self, choices, state):
        choices_id = []
        for c in choices:
            if c is None:
                choices_id.append(c)
            else:
                choices_id.append(c.get_id())

        sections_id = [a for a in self.q_values[state].keys()]
        values_id = [self.q_values[state][key] for key in sections_id if key in choices_id if self.q_values[state][key] is not None]

        #remove choices that have lead to None
        _choices = []
        for c in choices:
            if c is None:
                _choices.append(c)
            elif c in self.q_values[state].keys():
                v = self.q_values[state][c]
                if v is not None:
                    _choices.append(c)
            else:
                _choices.append(c)

        choices = _choices
        if random.uniform(0, 1) < self.epsilon or len(values_id) == 0:
            action = random.choice(choices)  # Explore action space
        else:

            ids = np.argmax(values_id)
            _id = ids
            section_id = sections_id[_id]  # Exploit learned values
            for choice in choices:
                if choice is None:
                    if choice == section_id:
                        return choice
                else:
                    if choice.get_id() == section_id:
                        return choice
            raise Exception("ERROR")
        return action

    def update_table(self, previous_state, current_state, section, reward=None, blocked=False):
        # state_id
        # logging.info("previous state %s" % previous_state)
        # logging.info("current state %s" % current_state)
        # logging.info("action %s" % section)
        old_value = self.q_values[previous_state][section.get_id()]

        values = []
        for key in self.q_values[current_state].keys():
            values.append(self.q_values[current_state][key])

        if len(values) == 0:
            next_max = 0
        else:
            next_max = np.max(values)

        if reward is None:
            reward = -section.calc_penalty()
        new_value = (1 - self.alpha) * old_value + self.alpha * (reward + self.gamma * next_max)

        if blocked:
            new_value = None
        self.q_values[previous_state, section.get_id()] = new_value


def get_state_id(section_id, train, trains):
    _hash = "%s-%s+" % (train, section_id)
    for _train in trains:
        if _train == train:
            continue
        __hash = "+"
        if len(_train.solution.sections) > 0:
            __hash = _train.solution.sections[-1].get_id()
        _hash += "%s-" % __hash

    return _hash


class Algorithm(object):
    def __init__(self):

        self.all_epochs = []
        self.all_penalties = []

    def train(self):
        for i in range(1, 100001):
            # state = env.reset()

            epochs, penalties, reward, = 0, 0, 0
            done = False

            while not done:

                # action = get_action(on_section)

                # next_state, reward, done, info = env.step(action)

                if reward == -10:
                    penalties += 1

                # state = next_state
                epochs += 1

            if i % 100 == 0:
                # clear_output(wait=True)
                pass  # print(f"Episode: {i}")

        print("Training finished.\n")

    def run(self):
        total_epochs, total_penalties = 0, 0
        episodes = 100

        for _ in range(episodes):
            epochs, penalties, reward = 0, 0, 0

            done = False

            while not done:
                # action = np.argmax(q_table[state])
                # state, reward, done, info = env.step(action)

                if reward == -10:
                    penalties += 1

                epochs += 1

            total_penalties += penalties
            total_epochs += epochs

        # print(f"Results after {episodes} episodes:")
        # print(f"Average timesteps per episode: {total_epochs / episodes}")
        # print(f"Average penalties per episode: {total_penalties / episodes}")
