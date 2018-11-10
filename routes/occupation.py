class Occupation(object):
    def __init__(self, data, section):
        self._data = data
        #will be in simulator assigned
        self.resource = None
        self.id = self._data["resource"]

    def get_resource_id(self):
        return self.id

    def get_resource(self):
        return self.resource

    #def get_direction(self):
    #    return self._data["occupation_direction"]