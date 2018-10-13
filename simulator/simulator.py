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
from trains.solution import Solution
from simulator.qtable import QTable, get_state_id, get_state_avoid_id
import numpy as np
from network.dijkstra import dijkstra
import random


class BlockinException(Exception):
    pass


class Simulator(object):
    def __init__(self, path, qtable):
        self.timetable = Timetable(json_path=path)
        self.resources = self.timetable.resources
        self.trains = list(self.timetable.trains.values())
        self.dispachter = Dispatcher(sim=self)

        self.waiting = set()
        self.events = defaultdict(list)
        self.qtable = qtable

        self.current_time = 0
        self.min_time = 9999999
        self.max_time = 0
        self.wait_time = 10.0

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
            for section in train.solution.sections[1:]:
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
        self.waiting = set()
        self.events = defaultdict(list)
        self.assign_sections_to_resources()

        self.match_trains()
        self.current_time = 0
        self.min_time = 9999999
        self.max_time = 0

        for train in self.trains:
            event = train.get_start_event()
            self.register_event(event)
            train.solution.sections = []
            train.solution.states = []
            train.solution.done = False

    def match_trains(self):
        resources = {}
        for train in self.trains:
            resources[train.get_id()] = set([r.get_id() for s in train.get_sections() for r in s.get_resources()])

        for train in self.trains:
            _trains = []
            rs = resources[train.get_id()]
            for _train in self.trains:
                _rs = resources[_train.get_id()]
                if len(_rs.intersection(rs)) > 0:
                    _trains.append(_train)
            train.other_trains = _trains

            train.connection_trains = set()
            for s in train.network.sections.values():
                if s.get_requirement() is not None:
                    for id in s.get_requirement().get_connections():
                        c_t = self.get_train(id)
                        if c_t is not None:
                            train.connection_trains.add(c_t)
            train.connection_trains = list(train.connection_trains)

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

        elif isinstance(event, ReleaseResourceEvent):
            self.release_resources(resource=event.resource, emited_at=event.emited_at)

        elif isinstance(event, EnterStationEvent):
            train = event.train
            section = event.section
            duration = section.get_requirement().get_min_stopping_time()
            earliest_exit = section.get_requirement().get_exit_earliest()
            time = max(earliest_exit, event.time + duration)
            next_event = EnterNodeEvent(time=time, train=train, node=section.end_node, previous_section=section)
            self.register_event(next_event)

    def run(self):
        self.current_time = self.min_time
        while self.current_time < self.max_time + 10:
            for event in self.events[self.current_time]:
                self.run_next(event=event)
            self.current_time += 1

        logging.info("Done %s" % self.compute_score())

    def avoid(self, state, action, causing_train):
        logging.info("Because of %s on %s > Avoid %s on %s" % (
            causing_train, causing_train.solution.sections[-1], action, state))
        self.qtable.to_avoid[state].add(action)
        if state in self.qtable.q_values:
            if action in self.qtable.q_values[state]:
                del self.qtable.q_values[state]

    def is_late(self, event):
        #return event.time > event.node.limit + self.max_delta
        section = event.previous_section
        t_out = section.entry_time + section.get_minimum_running_time()
        requirement = section.get_requirement()
        if requirement is not None:
            t_out += requirement.get_min_stopping_time()
            t_out = max(requirement.get_exit_earliest(), t_out)
        return event.time > t_out + self.max_delta

    def on_node(self, event):
        state = get_state_id(event.train, self)  # self.trains)
        state_to_avoid = get_state_avoid_id(event.train, self)  # self.trains)

        links = list(event.node.out_links)
        if len(links) == 0:
            event.train.solution.done = True
            self.go_to_section(from_section=event.previous_section, to_section=None, at=event.time)
            self.update(train=event.train, state=state)
            return

        links = [l for l in links if l.get_id() not in self.qtable.to_avoid[state_to_avoid]]

        if len(links) == 0:
            event.time += self.wait_time
            self.register_event(event)
            return

        link = self.qtable.get_action(links, state)

        if not link.is_free():
            if self.is_late(event):

                _trains = [t for t in link.block_by() if t != event.train]
                for t in _trains:
                    if len(t.solution.states)>1:
                        c_state = t.solution.states[-1]
                        p_state = t.solution.states[-2]
                        p_action = t.solution.sections[-2]
                        self.qtable.update_table(previous_state=p_state, previous_action=p_action, current_state=c_state, reward=-1)
                    self.avoid(t.solution.states_to_avoid[-1], t.solution.sections[-1].get_id(), event.train)

                raise BlockinException()

            event.time += self.wait_time
            self.register_event(event)
            return

        # can I already enter this link?
        if link.get_requirement() is not None and link.get_requirement().get_entry_earliest() is not None and event.time < link.get_requirement().get_entry_earliest():
            event = link.get_requirement().get_entry_earliest()
            self.register_event(event)
            assert False

        # can I already leave previous_section? or should I wait for a connecting train?
        if event.previous_section is not None:
            r = event.previous_section.get_requirement()
            if r is not None:
                for c in r.get_connections():
                    connecting_train = self.get_train(c.get_onto_service_intention())
                    marker = c.get_onto_section_marker()
                    _s = None
                    for c_s in connecting_train.solution.sections:
                        if c_s.marker == marker:
                            _s = c_s
                            break
                    if _s is None:
                        #conencting train did not yet arrived. Need to wait..
                        event.time += self.wait_time
                        self.register_event(event)
                        return
                    else:
                        #connection train is or has been on the section, check min time
                        t2 = (_s.entry_time+_s.get_requirement().get_min_stopping_time())
                        should_wait = t2-event.time<c.get_min_connection_time()
                        if should_wait:
                            event.time += self.wait_time
                            self.register_event(event)
                            return

        self.go_to_section(from_section=event.previous_section, to_section=link, at=event.time)

        self.update(train=event.train, state=state)

        event.train.solution.sections.append(link)
        event.train.solution.states.append(state)
        event.train.solution.states_to_avoid.append(state_to_avoid)

    def assign_limit(self):
        for train in self.trains:
            distances = dijkstra(source="start", dest="end", train=train)

            l = list(train.network.nodes["end"].in_links)[0]
            r = l.get_requirement()
            for n in train.network.nodes.values():
                n.limit = r.get_exit_latest() - (distances["end"] - distances[n.label])

    def free_all_resources(self):
        for train in self.trains:
            for s in train.network.sections.values():
                for r in s.get_resources():
                    r.free = True
                    r.currently_used_by = None

    def update(self, train, state):
        if len(train.solution.sections) > 0:
            p_state = train.solution.states[-1]
            last_action = train.solution.sections[-1]
            reward = - last_action.calc_penalty()
            self.qtable.update_table(p_state, current_state=state, previous_action=last_action, reward=reward)

    def go_to_section(self, from_section, to_section, at):
        to_resources = []

        if to_section is not None:
            to_resources = [r for r in to_section.get_resources()]
            to_section.entry_time = at

        # release previous section
        if from_section is not None:
            from_section.exit_time = at
            for from_r in from_section.get_resources():
                if from_r not in to_resources:
                    from_r.currently_used_by = None
                    from_r.last_exit_time = at
                    next_event = ReleaseResourceEvent(train=from_section.train, time=at + from_r.get_release_time(),
                                                      emited_at=at, resource=from_r)
                    self.register_event(next_event)

        # block next section
        for to_r in to_resources:
            to_r.block(train=to_section.train)

        if to_section is not None:
            # register next event: EnterNode or EnterStation
            requirement = to_section.get_requirement()
            next_time = to_section.get_minimum_running_time() + at
            if isinstance(requirement, HaltRequirement):
                earliest_entry = to_section.get_requirement().get_entry_earliest()
                # this test should be done before
                time = max(earliest_entry, next_time)
                self.register_event(EnterStationEvent(time=time, section=to_section, train=to_section.train))
            else:
                self.register_event(EnterNodeEvent(time=next_time, train=to_section.train, node=to_section.end_node,
                                                   previous_section=to_section))

    def release_resources(self, resource, emited_at):
        resource.release(release_time=emited_at)

    def register_event(self, event):
        self.min_time = min(self.min_time, event.time)
        self.max_time = max(self.max_time, event.time)
        self.events[event.time].append(event)

    def get_train(self, name):
        for train in self.trains:
            if train.get_id() == name:
                return train
