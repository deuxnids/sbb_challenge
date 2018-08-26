import isodate
from routes.occupation import Occupation


class Section(object):
    def __init__(self, data, path):
        self._data = data
        self.path = path
        self.train = path._route.train
        self.entry_time = 9999999
        self.exit_time = 9999999
        self.start_node = None
        self.end_node = None
        self.occupations = [Occupation(data=d, section=self) for d in self._data["resource_occupations"]]
        self.marker = None
        if "section_marker" in self._data:
            markers = self._data["section_marker"]
            if len(markers) > 0:
                self.marker = markers[0]

        self.requirement = None
        requirements = [r for r in self.train.get_requirements() if r.get_section_marker() == self.get_marker()]
        if len(requirements) > 0:
            self.requirement = requirements[0]

    def __repr__(self):
        return "Section(id=%s)" % (self.get_id())

    def get_id(self):
        return "%s#%s" % (self.path._route.get_id(), self.get_number())

    def get_number(self):
        """an ordering number.
        The train passes over the route_sections in this order. This is necessary because the JSON specification does not guarantee that the sequence in the file is preserved when deserializing.
        """
        return self._data["sequence_number"]

    def get_penalty(self):
        """used in the objective function for the timetable.
        If a train uses this route_section, this penalty accrues.  This field is optional. If it is not present, this is equivalent to penalty = 0.
        """
        key = "penalty"
        if key in self._data:
            value = self._data[key]
            if value is None:
                return 0.0
            else:
                return value
        return 0.0

    def get_route_alternative_marker_at_exit(self):
        key = "route_alternative_marker_at_exit"
        if key in self._data:
            return self._data[key][0]

    def get_route_alternative_marker_at_entry(self):
        key = "route_alternative_marker_at_entry"
        if key in self._data:
            return self._data[key][0]

    def get_minimum_running_time(self):
        """minimum time (duration) the train must spend on this route_section
        """
        return isodate.parse_duration(self._data["minimum_running_time"]).seconds

    def get_occupations(self):
        return self.occupations

    def get_resources(self):
        resources = []
        for o in self.get_occupations():
            resources.append(o.resource)
        return resources

    def get_marker(self):
        """labels that mark this route_section as a potential section to fulfil a section_requirement that has any of these as section_marker.
        Note: In all our problem instances, each route_section has at most one section_marker, i.e. the list has length at most one.
        """
        return self.marker

    def get_requirement(self):
        """
        assuming there is only at most one requirement
        :param train:
        :return:
        """
        return self.requirement

    def is_free(self):
        for r in self.get_resources():
            if not r.is_free_for(train=self.train):
                return False
        return True
