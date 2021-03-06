import isodate


class Connection(object):
    def __init__(self, data):
        self._data = data
        self.min_connection_time = isodate.parse_duration(self._data["min_connection_time"]).seconds

    def get_id(self):
        return self._data["id"]

    def get_onto_service_intention(self):
        """reference to the service_intention that accepts the connection"""
        return self._data["onto_service_intention"]

    def get_onto_section_marker(self):
        """reference to a section marker. Specifies which route_sections in the onto_service_intention are candidates to fulfil the connection"""
        return self._data["onto_section_marker"]

    def get_min_connection_time(self):
        return self.min_connection_time


class WaitingConnection(object):
    def __init__(self, from_train, from_section_marker, min_time):
        self.from_train = from_train
        self.from_section_marker = from_section_marker
        self.min_connection_time = min_time

    def get_id(self):
        return "%s_%s" % (self.from_train.get_id(), self.from_section_marker)

    def __hash__(self):
        return hash(self.get_id())

    def __str__(self):
        return "%s %s" % self.from_section_marker, self.min_connection_time
