import isodate


class Resource(object):
    def __init__(self, data):
        self._data = data
        self.id = self._data["id"]
        self.sections = []

    def get_id(self):
        return self.id

    def __eq__(self, other):
        return self.get_id() == other.get_id()

    def get_release_time(self):
        """
        describes how much time must pass between release of a resource by one train and the following occupation by the next train. See Business Rules for details.
        """
        return isodate.parse_duration(self._data["release_time"]).seconds

    def get_following_allowed(self):
        """flag whether the resource is of following type (true) or of blocking type (false).
        As mentioned, all resources in all the provided problem instances have this field set to false
        """
        return self._data["following_allowed"]

    def __str__(self):
        return "%s (%i s)" %(self.get_id(), self.get_release_time())