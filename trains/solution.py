from simulator.event import humanize_time


class Solution(object):
    def __init__(self, train):
        self.train = train
        self.sections = []
        self._entry_time = None

    def enter_node_event(self, event):
        section = event.previous_section
        if section is not None:
            section.exit_time = event.time
            section.entry_time = self._entry_time
            self._entry_time = None
            self.sections.append(section)

    def compute_objective(self):
        value = 0.0
        for section in self.sections:
            requirement = section.get_requirement()
            if requirement is not None:
                v = requirement.get_entry_delay_weight() * max(0, section.entry_time - requirement.get_entry_latest())
                value += v
                v = requirement.get_exit_delay_weight() * max(0, section.exit_time - requirement.get_exit_latest())
                value += v

        value = 1 / 60.0 * value

        for section in self.sections:
            value += section.get_penalty()

        return value
