from routes.section import Section


class Path(object):
    def __init__(self, data, route):
        self._data = data
        self._route = route
        self.sections = [Section(d, self) for d in self._data["route_sections"]]

    def get_id(self):
        return self._data["id"]

    def get_sections(self):
        return self.sections
