import isodate
import numpy as np
import logging
from simulator.event import humanize_time

from trains.connection import Connection


"""
{'sequence_number': 1, 'section_marker': 'A', 'type': 'start', 'entry_earliest': '08:20:00', 'entry_delay_weight': 1,                              'exit_delay_weight': 1, 'connections': None}
{'sequence_number': 2, 'section_marker': 'B', 'type': 'halt',  'min_stopping_time': 'PT3M',  'entry_delay_weight': 1, 'exit_earliest': '08:30:00', 'exit_delay_weight': 1, 'connections': None}
{'sequence_number': 3, 'section_marker': 'C', 'type': 'ende',                                'entry_delay_weight': 1, 'exit_latest': '08:50:00',   'exit_delay_weight': 1, 'connections': None}
"""


class Requirement(object):

    def __init__(self, data, train):
        self._data = data
        self.train = train
        self.waiting_connections = []
        self.min_stopping_time= 0.0

        key = "min_stopping_time"
        if key in self._data:
            self.min_stopping_time =  isodate.parse_duration(self._data["min_stopping_time"]).seconds


    @staticmethod
    def factory(data, **kwargs):
        _type = data["type"]
        if _type == "start":
            return StartRequirement(data=data, **kwargs)
        elif _type == "halt":
            return HaltRequirement(data=data, **kwargs)
        elif _type == "ende":
            return EndeRequirement(data=data, **kwargs)

        return Requirement(data=data, **kwargs)

    def get_type(self):
        """a text field describing what this requirement is meant to represent, such as start of a train, a scheduled stop, etc. Has no effect on processing. You may ignore it.
        """
        return self._data["type"]

    def get_section_marker(self):
        return self._data["section_marker"]

    def get_sequence_number(self):
        return self._data["sequence_number"]

    def get_min_stopping_time(self):
        return self.min_stopping_time

    def get_entry_earliest(self):
        key = "entry_earliest"
        if key in self._data:
            return to_sec(self._data[key])
        return 0.0

    def get_exit_earliest(self):
        key = "exit_earliest"
        if key in self._data:
            return to_sec(self._data[key])
        return 0.0

    def get_entry_latest(self):
        key = "entry_latest"
        if key in self._data:
            return to_sec(self._data[key])
        return 24*60*60*3

    def get_exit_latest(self):
        key = "exit_latest"
        if key in self._data:
            return to_sec(self._data[key])
        return 24*60*60*3

    def get_connections(self):
        if "connections" not in self._data:
            return []
        if self._data["connections"] is None:
            return []
        return [Connection(c) for c in self._data["connections"] if c is not None]

    def get_entry_delay_weight(self):
        key = "entry_delay_weight"
        if key in self._data:
            return self._data[key]
        return 0.0

    def get_exit_delay_weight(self):
        key = "exit_delay_weight"
        if key in self._data:
            return self._data[key]
        return 0.0

    def __str__(self):
        return "Halt:  %s<->%s (%s) %s<->%s" % (humanize_time(self.get_entry_earliest()),
                                            humanize_time(self.get_entry_latest()),
                                            humanize_time(self.get_min_stopping_time()),
                                            humanize_time(self.get_exit_earliest()),
                                            humanize_time(self.get_exit_latest()))



class StartRequirement(Requirement):
    def __init__(self, **kwargs):
        Requirement.__init__(self, **kwargs)


class HaltRequirement(Requirement):
    def __init__(self, **kwargs):
        Requirement.__init__(self, **kwargs)


class EndeRequirement(Requirement):
    def __init__(self, **kwargs):
        Requirement.__init__(self, **kwargs)


def to_sec(txt):
    a = txt.split(":")
    return int(a[0])*60*60 + int(a[1])*60 + int(a[2])