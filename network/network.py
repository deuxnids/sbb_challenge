import logging
import copy
from network.node import Node


class Network(object):
    def __init__(self):
        self.nodes = {}
        self.sections = {}

    def create(self, timetable):
        for route in timetable.routes.values():
            self.add_route(route)
        logging.info("%i Nodes created" % len(self.nodes.keys()))

    def _get_start_node_id(self, section, previous_section=None):
        marker = section.get_route_alternative_marker_at_entry()
        if marker is not None:
            return str(marker)
        elif previous_section is not None:
            return str(previous_section.get_number()) + "->" + str(section.get_number())
        else:
            return "start"

    def get_first_node(self):
        return self.nodes["start"]

    def _get_end_node_id(self, section, next_section=None):
        marker = section.get_route_alternative_marker_at_exit()
        if marker is not None:
            return str(marker)
        elif next_section is not None:
            return str(section.get_number()) + "->" + str(next_section.get_number())
        else:
            return "end"

    def add_route(self, route):
        for path in route.get_paths().values():
            sections = path.get_sections()
            n = len(sections)

            for i, section in enumerate(sorted(sections, key=lambda x: x.get_number())):
                previous_section = None
                next_section = None

                if i > 0:
                    previous_section = sections[i - 1]
                if i < n - 1:
                    next_section = sections[i + 1]

                start_id = self._get_start_node_id(section, previous_section=previous_section)
                end_id = self._get_end_node_id(section, next_section=next_section)

                if start_id not in self.nodes:
                    self.nodes[start_id] = Node(label=start_id)
                if end_id not in self.nodes:
                    self.nodes[end_id] = Node(label=end_id)

                start_node = self.nodes[start_id]
                end_node = self.nodes[end_id]

                section.start_node = start_node
                section.end_node = end_node

                end_node.in_links.add(section)
                start_node.out_links.add(section)

                self.sections[section.get_number()] = section


