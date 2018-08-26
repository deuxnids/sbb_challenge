from simulator.event import humanize_time

MAX_TIME = 24 * 60 * 60


class Solution(object):
    def __init__(self, train):
        self.train = train
        self.sections = []
        self._entry_time = None

    def leave_section(self, exit_time):
        self.sections[-1].exit_time = exit_time

    def enter_section(self, section, entry_time):
        if len(self.sections)>0:
            self.sections[-1].exit_time = entry_time
        section.entry_time = entry_time
        self.sections.append(section)

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
