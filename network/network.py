import logging
import copy
from network.node import Node
from routes.section import Section


class Network(object):
    def __init__(self):
        self.nodes = {}
        self.sections = {}

    def create(self, timetable):
        for route in timetable.routes.values():
            self.add_route(route)
        logging.info("%i Nodes created" % len(self.nodes.keys()))

    def from_node_id(self, route_path, route_section, index_in_path):
        if "route_alternative_marker_at_entry" in route_section.keys() and \
                route_section["route_alternative_marker_at_entry"] is not None and \
                len(route_section["route_alternative_marker_at_entry"]) > 0:
            return "(" + str(route_section["route_alternative_marker_at_entry"][0]) + ")"
        else:
            if index_in_path == 0:  # can only get here if this node is a very beginning of a route
                return "start"
            else:
                return "(" + (str(route_path["route_sections"][index_in_path - 1]["sequence_number"]) + "->" +
                              str(route_section["sequence_number"])) + ")"

    def to_node_id(self, route_path, route_section, index_in_path):
        if "route_alternative_marker_at_exit" in route_section.keys() and \
                route_section["route_alternative_marker_at_exit"] is not None and \
                len(route_section["route_alternative_marker_at_exit"]) > 0:

            return "(" + str(route_section["route_alternative_marker_at_exit"][0]) + ")"
        else:
            if index_in_path == (len(route_path["route_sections"]) - 1):  # meaning this node is a very end of a route
                return "end"
            else:
                return "(" + (str(route_section["sequence_number"]) + "->" +
                              str(route_path["route_sections"][index_in_path + 1]["sequence_number"])) + ")"

    def get_first_node(self):
        return self.nodes["depot"]

    def add_route(self, route):
        for path in route.get_paths().values():
            sections = path.get_sections()
            n = len(sections)

            for (i, section) in enumerate(sections):

                start_id = self.from_node_id(route_path=path._data, route_section=section._data, index_in_path=i)
                end_id = self.to_node_id(route_path=path._data, route_section=section._data, index_in_path=i)

                if start_id not in self.nodes:
                    self.nodes[start_id] = Node(label=start_id)
                if end_id not in self.nodes:
                    self.nodes[end_id] = Node(label=end_id)

                start_node = self.nodes[start_id]
                end_node = self.nodes[end_id]

                section.start_node = start_node
                section.end_node = end_node

                end_node.in_links.append(section)
                start_node.out_links.append(section)

                self.sections[section.get_number()] = section
        for node_id in self.nodes:
            node = self.nodes[node_id]
            if len(node.in_links) == 0:
                del self.nodes[node_id]
                node.label = "start"
                self.nodes["start"] = node
            if len(node.out_links) == 0:
                del self.nodes[node_id]
                node.label = "end"
                self.nodes["end"] = node

        start_node = Node(label="depot")
        end_node = self.nodes["start"]
        _section = list(end_node.out_links)[-1]
        _data = copy.deepcopy(_section._data)
        _data["sequence_number"] = -1
        _data["minimum_running_time"] = "PT1S"
        section = Section(data=_data, path=_section.path)
        section.start_node = start_node
        section.requirement = None
        section.occupations = []
        section.marker = "depot"
        section.end_node = end_node
        start_node.out_links.append(section)
        self.nodes["depot"] = start_node
        self.sections[section.get_number()] = section

        for section in self.sections.values():
            section.init_weights()
