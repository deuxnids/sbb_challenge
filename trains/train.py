from trains.requirement import Requirement
from network.network import Network
from simulator.event import EnterNodeEvent
from trains.solution import Solution


class Train(object):
    def __init__(self, data):
        self._data = data
        self.network = Network()
        self.solution = Solution(train=self)

    def get_id(self):
        return self._data["id"]

    def get_sections(self):
        return list(self.network.sections.values())

    def get_next_free_sections(self, node):
        n = len([s for s in node.out_links if s.is_free])
        n2 = len([s for s in node.out_links])
        print("%s %i/%i" % (self, n, n2))
        return [s for s in node.out_links if s.is_free]

    def get_requirements(self):
        """
        sorted list of requirements
        :return:
        """
        return sorted([Requirement.factory(data=d, train=self) for d in self._data["section_requirements"]],
                      key=lambda x: x.get_sequence_number())

    def get_start_event(self):
        requirement = self.get_requirements()[0]
        return EnterNodeEvent(train=self, node=self.network.get_first_node(), time=requirement.get_entry_earliest(),
                              previous_section=None)

    def __str__(self):
        return "Train %s" % self.get_id()

    def __eq__(self, other):
        return self.get_id() == other.get_id()
