class Event(object):
    def __init__(self, time, train):
        self.time = time
        self.train = train

    def __str__(self):
        return humanize_time(self.time) + " %s" % self.train


class EnterNodeEvent(Event):
    def __init__(self, node, previous_section, **kwargs):
        Event.__init__(self, **kwargs)
        self.node = node
        self.previous_section = previous_section

    def __str__(self):
        return super(EnterNodeEvent, self).__str__() + " enters %s coming from %s" % (self.node, self.previous_section)


class DestinationNodeEvent(Event):
    def __init__(self, node, previous_section, **kwargs):
        Event.__init__(self, **kwargs)
        self.node = node
        self.previous_section = previous_section

    def __str__(self):
        return super(DestinationNodeEvent, self).__str__() + " destination %s" % self.node


class LeaveNodeEvent(Event):
    def __init__(self, node, previous_section, **kwargs):
        Event.__init__(self, **kwargs)
        self.node = node
        self.previous_section = previous_section

    def __str__(self):
        return super(LeaveNodeEvent, self).__str__() + " leaves %s" % self.node


class EnterStationEvent(Event):
    def __init__(self, section, **kwargs):
        Event.__init__(self, **kwargs)
        self.section = section

    def __str__(self):
        return super(EnterStationEvent, self).__str__() + " enters station"


class LeaveStationEvent(Event):
    def __init__(self, section, **kwargs):
        Event.__init__(self, **kwargs)
        self.section = section

    def __str__(self):
        return super(LeaveStationEvent, self).__str__() + " leaves station"


class WaitingOnSection(Event):
    def __init__(self, node, section, **kwargs):
        self.node = node
        self.previous_section = section
        Event.__init__(self, **kwargs)

    def __str__(self):
        return super(WaitingOnSection, self).__str__() + " waiting"


class ReleaseResourceEvent(Event):
    def __init__(self, resource, **kwargs):
        Event.__init__(self, **kwargs)
        self.resource = resource

    def __str__(self):
        return super(ReleaseResourceEvent, self).__str__() + " release resource %s" % self.resource



def humanize_time(secs):
    if secs is None:
        return ""
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    return '%02d:%02d:%02d' % (hours, mins, secs)
