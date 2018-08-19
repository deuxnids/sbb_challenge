from routes.path import Path


class Route(object):
    def __init__(self, data, train):
        self._data = data
        self.train = train
        self.paths = {d["id"]: Path(d, self) for d in self._data["route_paths"]}

    def get_id(self):
        return self._data["id"]

    def get_paths(self):
        return self.paths

    def get_sections(self):
        sections = []
        for path in self.get_paths().values():
            sections += path.get_sections()
        return sections
