import isodate


class Connection(object):
    def __init__(self, data):
        self._data = data

    def get_id(self):
        return self._data["id"]

    def get_onto_service_intention(self):
        """reference to the service_intention that accepts the connection"""
        return self._data["onto_service_intention"]

    def get_onto_section_marker(self):
        """reference to a section marker. Specifies which route_sections in the onto_service_intention are candidates to fulfil the connection"""
        return self._data["onto_section_marker"]

    def get_min_connection_time(self):
        return isodate.parse_duration(self._data["min_connection_time"]).seconds
