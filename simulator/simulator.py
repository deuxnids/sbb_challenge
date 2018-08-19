import logging
from timetable import Timetable
from simulator.dispatcher import Dispatcher
from simulator.event import EnterNodeEvent
from simulator.event import LeaveNodeEvent
from simulator.event import EnterStationEvent
from simulator.event import LeaveStationEvent
from simulator.event import ReleaseResourceEvent
from simulator.event import WaitingOnSection
from trains.requirement import HaltRequirement
from simulator.event import humanize_time


class Simulator(object):
    def __init__(self, path):
        self.timetable = Timetable(json_path=path)
        self.resources = self.timetable.resources
        self.trains = list(self.timetable.trains.values())
        self.dispachter = Dispatcher()

        self.events = []

    def create_output(self):
        output = {
            "problem_instance_label": self.timetable.label,
            "problem_instance_hash": self.timetable.hash,
            "hash": self.timetable.hash,
            "train_runs":
                []
        }

        for train in self.trains:
            section_output = []
            for section in train.solution.sections:
                r = section.get_requirement()
                marker = None
                if r is not None:
                    marker = r.get_section_marker()
                section_output.append({
                    "entry_time": humanize_time(section.entry_time),
                    "exit_time": humanize_time(section.exit_time),
                    "route": section.train.get_id(),
                    "route_section_id": section.get_id(),
                    "route_path": section.path.get_id(),
                    "section_requirement": marker})

            _output = {"service_intention_id": train.get_id(), "train_run_sections": section_output}
            output["train_runs"].append(_output)
        return output

    def assign_sections_to_resources(self):
        for train in self.trains:
            for section in train.get_sections():
                for occupation in section.get_occupations():
                    resource_id = occupation.get_resource_id()
                    occupation.resource = self.resources[resource_id]
                    occupation.resource.sections.append(section)

    def initialize(self):
        self.events = []
        self.assign_sections_to_resources()
        for train in self.trains:
            event = train.get_start_event()
            self.register_event(event)

    def run(self):
        self.initialize()

        max_time = 24*60*60

        while len(self.events):
            event = self.events[0]
            if event.time>max_time:
                break

            self.events.remove(event)
            train = event.train

            print(event)

            if isinstance(event, EnterNodeEvent):
                # Depending on which a section can be picked
                # This is where the dispatcher is used
                # Waiting or LeavingNode
                self.on_node(event=event)
                train.solution.enter_node_event(event=event)

            if isinstance(event, LeaveNodeEvent):
                # = enterSection
                train.solution._entry_time = event.time
                self.release_previous_section(event=event)

            elif isinstance(event, WaitingOnSection):
                self.on_node(event=event)

            elif isinstance(event, ReleaseResourceEvent):
                self.free_sections(resource=event.resource, time=event.time)

            elif isinstance(event, EnterStationEvent):
                train = event.train
                section = event.section
                duration = section.get_requirement().get_min_stopping_time()
                earliest_exit = section.get_requirement().get_exit_earliest()
                time = max(earliest_exit, event.time + duration)
                next_event = LeaveStationEvent(time=time, train=train, section=section)
                self.register_event(next_event)

            elif isinstance(event, LeaveStationEvent):
                train = event.train
                section = event.section
                next_event = EnterNodeEvent(time=event.time, train=train, node=section.end_node,
                                            previous_section=section)
                self.register_event(next_event)

    def on_node(self, event):
        train = event.train

        if len(event.node.out_links) == 0:
            next_event = LeaveNodeEvent(time=event.time, node=event.node, train=train, previous_section=event.previous_section)
            self.register_event(next_event)

        else:
            sections = event.train.get_next_free_sections(node=event.node)

            if len(sections) == 0:
                next_event = WaitingOnSection(time=event.time + 30, train=train, node=event.node, section=event.previous_section)
                self.register_event(next_event)
                if len(train.solution.sections) > 0:
                    previous_section = train.solution.sections[-1]
                    # self.block_sections(train=train, occupations=previous_section.get_occupations(), time=event.time)

            else:
                section = self.dispachter.choose(sections)
                self.block_sections(train=train, section=section, time=event.time)

                next_event = LeaveNodeEvent(time=event.time, node=event.node, train=train, previous_section=event.previous_section)
                self.register_event(next_event)

                next_event = self.get_next_event(train=train, section=section, current_time=event.time)
                self.register_event(next_event)

    def release_previous_section(self, event):
        train = event.train
        if len(train.solution.sections) > 0:
            previous_section = train.solution.sections[-1]
            for occupation in previous_section.get_occupations():
                resource = occupation.get_resource()

                next_event = ReleaseResourceEvent(train=train,
                                                  time=event.time + resource.get_release_time(),
                                                  resource=resource)
                self.register_event(next_event)

    def get_next_event(self, train, section, current_time):
        requirement = section.get_requirement()
        next_time = section.get_minimum_running_time() + current_time
        if requirement is not None:
            if isinstance(requirement, HaltRequirement):
                earliest_entry = section.get_requirement().get_entry_earliest()
                time = max(earliest_entry, next_time)
                return EnterStationEvent(time=time, section=section, train=train)

        return EnterNodeEvent(time=next_time, train=train, node=section.end_node, previous_section=section)

    def block_sections(self, train, section, time):
        for ocupation in section.get_occupations():
            resource = ocupation.resource
            for _section in resource.sections:
                if _section.train == train:
                    continue
                _section.is_free = False
                _section.busy_till = max(_section.busy_till, time + resource.get_release_time())

    def free_sections(self, resource, time):
        for section in resource.sections:
            if time > section.busy_till:
                section.is_free = True

    def register_event(self, event):
        self.events.append(event)
        self.sort_events()

    def sort_events(self):
        self.events = sorted(self.events, key=lambda x: x.time, reverse=False)
