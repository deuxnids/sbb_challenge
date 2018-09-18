import logging
from timetable import Timetable
from simulator.dispatcher import Dispatcher
from simulator.event import EnterNodeEvent
from simulator.event import LeaveNodeEvent
from simulator.event import EnterStationEvent
from simulator.event import LeaveStationEvent
from simulator.event import ReleaseResourceEvent
from trains.requirement import HaltRequirement
from simulator.event import humanize_time
from collections import defaultdict


class Simulator(object):
    def __init__(self, path):
        self.timetable = Timetable(json_path=path)
        self.resources = self.timetable.resources
        self.trains = list(self.timetable.trains.values())
        self.dispachter = Dispatcher(sim=self)

        self.waiting = set()
        self.events = defaultdict(list)

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
        self.events = defaultdict(list)
        self.assign_sections_to_resources()
        for train in self.trains:
            event = train.get_start_event()
            self.register_event(event)

    def compute_score(self):
        score = 0
        for train in self.trains:
            score += train.solution.compute_objective()
        return score

    def run_next(self, event):

        if isinstance(event, EnterNodeEvent):
            # Depending on which a section can be picked
            # This is where the dispatcher is used
            # Waiting or LeavingNode
            self.on_node(event=event)

        elif isinstance(event, LeaveNodeEvent):
            self.register_release_event(event=event)

        elif isinstance(event, ReleaseResourceEvent):
            self.release_resources(resource=event.resource, emited_at=event.emited_at)

        elif isinstance(event, EnterStationEvent):
            train = event.train
            section = event.section
            duration = section.get_requirement().get_min_stopping_time()
            earliest_exit = section.get_requirement().get_exit_earliest()
            time = max(earliest_exit, event.time + duration)
            next_event = LeaveStationEvent(time=time + 1, train=train, section=section)
            self.register_event(next_event)

        elif isinstance(event, LeaveStationEvent):
            train = event.train
            section = event.section
            next_event = EnterNodeEvent(time=event.time + 1, train=train, node=section.end_node,
                                        previous_section=section)
            self.register_event(next_event)

    def run(self):
        i = 6 * 60 * 60
        while i < 10 * 60 * 60:
            i += 1
            for event in self.events[i]:
                print(event)
                self.run_next(event=event)

        print("Done %s" % self.compute_score())

    def on_node(self, event):
        train = event.train

        # We are at the end of the journey
        if len(event.node.out_links) == 0:
            next_event = LeaveNodeEvent(time=event.time + 1, node=event.node, train=train,
                                        previous_section=event.previous_section, next_section=None)
            self.register_event(next_event)
            train.solution.leave_section(exit_time=event.time)
            logging.info("%s done" % train)
            return

        # We still have a few section to visit
        else:
            sections = event.train.get_next_free_sections(node=event.node)
            if len(sections) == 0:
                sections.append(None)
                # train is blocked, is the other train also blocked? if yes throw error
            section = self.dispachter.choose(sections, train)
            if section is None:
                for blocking_train_id in train.blocked_by():
                    blocking_train = self.get_train(blocking_train_id)

                    if train.get_id() in blocking_train.blocked_by():
                        raise Exception("mutual blocking %s<->%s" % (train, blocking_train))

                self.waiting.add(train.get_id())
                next_event = EnterNodeEvent(train=train, time=event.time + 30, previous_section=event.previous_section,
                                            node=event.node)
                self.register_event(next_event)
                return

            else:

                if train.get_id() in self.waiting:
                    self.waiting.remove(train.get_id())

                train.solution.enter_section(section, entry_time=event.time)
                # print("b", section, [str(r) for r in section.get_resources()])
                self.block_resources(train=train, section=section)

                next_event = LeaveNodeEvent(time=event.time, node=event.node, train=train,
                                            previous_section=event.previous_section, next_section=section)
                self.register_event(next_event)

                next_event = self.get_next_event(train=train, section=section, current_time=event.time)
                self.register_event(next_event)
                return

    def register_release_event(self, event):
        train = event.train
        section = event.previous_section
        next_section = event.next_section
        next_resources = []
        if next_section is not None:
            next_resources = [r for r in next_section.get_resources()]

        # logging.info(humanize_time(event.time) + " releasing %s % s" % (section, train))
        if section is not None:
            for resource in section.get_resources():
                if resource in next_resources:
                    continue
                # print(humanize_time(event.time), "Emiting release", train, resource)
                resource.currently_used_by = None
                resource.last_exit_time = event.time
                next_event = ReleaseResourceEvent(train=train,
                                                  time=event.time + resource.get_release_time(),
                                                  emited_at=event.time,
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

    def block_resources(self, train, section):
        for resource in section.get_resources():
            resource.block(train=train)

    def release_resources(self, resource, emited_at):
        resource.release(release_time=emited_at)

    def register_event(self, event):
        self.events[event.time].append(event)

    def get_train(self, name):
        for train in self.trains:
            if train.get_id() == name:
                return train
