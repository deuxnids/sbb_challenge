from trains.requirement import Requirement
from network.network import Network
from simulator.event import EnterNodeEvent
from trains.solution import Solution
import copy
import numpy as np

class Train(object):
    def __init__(self, data):
        self._data = data
        self.network = Network()
        self.solution = Solution(train=self)
        self.requirements = None
        self.id = self._data["id"]

    def get_id(self):
        return self.id

    def get_sections(self):
        return list(self.network.sections.values())

    def get_next_sections(self):
        if len(self.solution.sections) == 0:
            node = self.get_first_node()
        else:
            node = self.solution.sections[-1].end_node
        return list(node.out_links)

    def blocked_by(self):
        sections = self.get_next_sections()
        ids = list(set([r.currently_used_by.get_id() for s in sections for r in s.get_resources() if
                        r.currently_used_by is not None]))
        if self.get_id() in ids:
            ids.remove(self.get_id())
        return ids

    def get_next_free_sections(self, node):
        free_sections = [s for s in node.out_links if s.is_free()]
        return free_sections

    def get_requirements(self):
        """
        sorted list of requirements
        :return:
        """

        if self.requirements is None:
            self.requirements = sorted(
                [Requirement.factory(data=d, train=self) for d in self._data["section_requirements"]],
                key=lambda x: x.get_sequence_number())
        return self.requirements

    def get_start_event(self):
        requirement = self.get_requirements()[0]
        return EnterNodeEvent(train=self, node=self.get_first_node(), time=requirement.get_entry_earliest()-1,
                              previous_section=None)

    def get_first_node(self):
        return self.network.get_first_node()

    def __str__(self):
        return "Train %s" % self.get_id()

    def __eq__(self, other):
        return self.get_id() == other.get_id()

    def compute_routes(self, start_node=None, limit=np.inf):

        def explore_node(node, links, routes):
            for link in node.out_links:
                _links = copy.copy(links)
                _links.append(link)
                if link.end_node.label == "end" or len(_links)>limit:
                    routes.append(_links)
                else:
                    node = link.end_node
                    explore_node(node, _links, routes)

        routes = []
        if start_node is None:
            start_node = self.get_first_node()
        explore_node(start_node, [], routes)
        return routes