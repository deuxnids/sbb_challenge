from simulator.event import humanize_time
import numpy as np

MAX_TIME = 24 * 60 * 60


class SectionSolution(object):
    def __init__(self, section):
        self.section = section
        self.entry_time = np.inf
        self.exit_time = np.inf
        self.train = section.train

    def __str__(self):
        return "%s (%s -> %s)" % (self.section, humanize_time(self.entry_time), humanize_time(self.exit_time))

    def nominal_exit_time(self):
        t_out = self.entry_time + self.section.get_minimum_running_time()
        requirement = self.section.get_requirement()
        if requirement is not None:
            t_out += requirement.get_min_stopping_time()
            t_out = max(requirement.get_exit_earliest(), t_out)
        return t_out

    def get_resources(self):
        return self.section.get_resources()

    def calc_penalty(self):
        value = 0.0

        requirement = self.section.get_requirement()
        if requirement is not None:
            v = requirement.get_entry_delay_weight() * max(0, self.entry_time - requirement.get_entry_latest())
            value += v
            v = requirement.get_exit_delay_weight() * max(0, self.exit_time - requirement.get_exit_latest())
            value += v

        value = 1 / 60.0 * value
        value += self.section.get_penalty()

        return value

    def get_id(self):
        return self.section.get_id()

    def get_end_node(self):
        return self.section.end_node

    def get_marker(self):
        return self.section.marker

    def get_requirement(self):
        return self.section.get_requirement()

    def get_minimum_running_time(self):
        return self.section.get_minimum_running_time()

    def get_penalty(self):
        return self.section.get_penalty()

    def get_path(self):
        return self.section.path


class Solution(object):
    def __init__(self, train):
        self.train = train
        c_section = SectionSolution(train.network.nodes["depot"].out_links[0])
        c_section.entry_time = -np.inf
        self.done = False

        self.sections = [c_section]
        self.other_trains_sections = [{}]

        self.states = [None]

    def __str__(self):
        return "%s : %s" % (self.train, "->".join(self.sections))

    def get_current_section(self):
        return self.sections[-1]

    def compute_objective(self):
        value = 0.0

        sections = {}
        for section in self.sections:
            requirement = section.get_requirement()
            if requirement is not None:
                sections[requirement] = section

        for requirement in self.train.get_requirements():
            if requirement in sections:
                section = sections[requirement]
                v = requirement.get_entry_delay_weight() * max(0, section.entry_time - requirement.get_entry_latest())
                value += v
                v = requirement.get_exit_delay_weight() * max(0, section.exit_time - requirement.get_exit_latest())
                value += v
            else:
                v = requirement.get_entry_delay_weight() * max(0, MAX_TIME - requirement.get_entry_latest())
                value += v
                v = requirement.get_exit_delay_weight() * max(0, MAX_TIME - requirement.get_exit_latest())
                value += v

        value = 1 / 60.0 * value

        for section in self.sections:
            value += section.get_penalty()

        return value

    def save_states(self, section, state):
        self.sections.append(section)
        self.other_trains_sections.append({t: t.solution.sections[-1] for t in self.train.other_trains if len(t.solution.sections) > 0})
        self.states.append(state)
