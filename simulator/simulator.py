import logging
import numpy as np
import random
import itertools

from timetable import Timetable
from simulator.event import EnterNodeEvent
from simulator.event import EnterStationEvent
from simulator.event import ReleaseResourceEvent
from trains.requirement import HaltRequirement
from simulator.event import humanize_time
from collections import defaultdict
from simulator.qtable import get_state_id
from network.dijkstra import dijkstra
from trains.connection import WaitingConnection
from trains.solution import Solution, SectionSolution


class BlockinException(Exception):
    def __init__(self, back_time, n):
        self.n = n
        self.back_time = back_time


class Simulator(object):
    def __init__(self, path, qtable):
        self.timetable = Timetable(json_path=path)
        self.resources = self.timetable.resources
        self.trains = list(self.timetable.trains.values())

        self.events = defaultdict(list)
        self.qtable = qtable

        self.current_time = 0
        self.min_time = 9999999
        self.max_time = 0
        self.wait_time = 10.0
        self.done = False
        self.late_on_node = False

        self.with_connections = True
        self.max_delta = 60 * 30

        self.priorities = {}
        self.blocked_trains = set()

        self.assign_sections_to_resources()

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
                    "route_path": section.get_path().get_id(),
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

        self.done = False
        self.current_time = 0
        self.min_time = 9999999
        self.max_time = 0

        for train in self.trains:
            event = train.get_start_event()
            self.register_event(event)
            train.solution = Solution(train=train)

    def match_trains(self):
        resources = {}
        for train in self.trains:
            resources[train.get_id()] = set([r.get_id() for s in train.get_sections() for r in s.get_resources()])

        delta = 60 * 60

        for i, train in enumerate(sorted(self.trains, key=lambda x: len(x.get_requirements()))):
            train.int_id = i

        #for train1, train2 in itertools.combinations(self.trains, 2):
        #    trains_pair = tuple(sorted((train1.int_id, train2.int_id)))

        #    if trains_pair not in self.priorities:
        #        a = sorted([train1, train2],
        #                   key=lambda t: t.network.nodes["end"].limit - t.network.nodes["start"].limit, reverse=True)
         #       self.priorities[trains_pair] = a

        for i, train in enumerate(self.trains):
            _trains = []
            start = train.network.nodes["start"].limit
            stop = train.network.nodes["end"].limit
            rs = resources[train.get_id()]
            for _train in self.trains:
                _rs = resources[_train.get_id()]
                if len(_rs.intersection(rs)) > 0:
                    _start = _train.network.nodes["start"].limit
                    _stop = _train.network.nodes["end"].limit

                    if (start - delta <= _stop <= stop + delta) or (_start - delta <= stop <= _stop + delta):
                        _trains.append(_train)
            train.other_trains = _trains

        # is this used?
        # for train in self.trains:

        #    train.connection_trains = set()
        #    for s in train.network.sections.values():
        #        if s.get_requirement() is not None:
        #            for id in s.get_requirement().get_connections():
        #                c_t = self.get_train(id)
        #                # if c_t is not None:
        #                train.connection_trains.add(c_t)
        #    train.connection_trains = list(train.connection_trains)

    def spiegel_anschlusse(self):
        for train in self.trains:
            for s in train.network.sections.values():
                r = s.get_requirement()
                if r is not None:
                    for c in r.get_connections():
                        wc = WaitingConnection(from_train=train, from_section_marker=s.marker,
                                               min_time=c.get_min_connection_time())
                        to_train = self.get_train(c.get_onto_service_intention())
                        marker = c.get_onto_section_marker()
                        for _s in to_train.network.sections.values():
                            if _s.marker == marker:
                                assert _s.get_requirement() is not None
                                _r = _s.get_requirement()
                                _r.waiting_connections.append(wc)

        for train in self.trains:
            for r in train.get_requirements():
                con = {}
                for wc in r.waiting_connections:
                    con[wc.get_id()] = wc
                r.waiting_connections = list(con.values())

    def compute_score(self):
        score = 0
        for train in self.trains:
            score += train.solution.compute_objective()
        return score

    def run_next(self, event):
        if isinstance(event, EnterNodeEvent):
            self.on_node(event=event)

        elif isinstance(event, ReleaseResourceEvent):
            resource = event.resource
            resource.release(train=event.train, release_time=event.emited_at)

        elif isinstance(event, EnterStationEvent):
            train = event.train
            section = event.section
            duration = section.get_requirement().get_min_stopping_time()
            earliest_exit = section.get_requirement().get_exit_earliest()
            time = max(earliest_exit, event.time + duration)
            next_event = EnterNodeEvent(time=time, train=train, node=section.get_end_node(),
                                        previous_section=section)
            self.register_event(next_event)

    def run(self):
        self.current_time = self.min_time
        while self.current_time < self.max_time + 10:
            if self.current_time > 60 * 60 * 25:
                logging.info("breaking")
                break
            for event in self.events[self.current_time]:
                self.run_next(event=event)
            del self.events[self.current_time]
            self.current_time += 1
        self.done = True
        logging.info("Done %s" % self.compute_score())

    def is_late_on_node(self, event):
        section = event.previous_section
        if section is None:
            return False
        t_out = section.nominal_exit_time()
        d = event.time > (t_out + self.max_delta)
        return d

    def is_late(self, event):
        if self.late_on_node:
            return self.is_late_on_node(event)
        else:
            ts = event.train.network.nodes["start"].limit
            tf = event.train.network.nodes["end"].limit
            tc = event.node.limit
            delta = np.interp(tc, [ts, tf], [self.min_delta, self.max_delta])
            return event.time > event.node.limit + delta

    def on_node(self, event):
        train = event.train
        section = train.solution.get_current_section()
        _links = event.node.out_links

        if train in self.blocked_trains:
            self.blocked_trains.add(train)

        if self.if_at_end(section, event):
            return

        # can I already leave previous_section? or should I wait for a connecting train?
        if self.check_connections(section, event):
            return

        if section is not None:
            _links = self.remove_link_to_avoid(_links, event.train)

        if len(_links) == 0:
            event.time += self.wait_time
            self.register_event(event)
            return

        links = [link for link in _links if link.is_free()]

        if self.check_if_free(links, _links, event):
            return


        state = get_state_id(train, self.n_state)
        link = self.qtable.get_action(links, state)

        # can I already enter this link?
        if self.check_earliest_entry(link, event):
            return

        to_section = SectionSolution(link)
        self.go_to_section(from_section=section, to_section=to_section, at=event.time)

        train.solution.save_states(section=to_section, state=state)
        self.update(train=event.train, state=state, time=event.time)

    def if_at_end(self, section, event):
        if event.node.label == "end":

            state = get_state_id(event.train, self.n_state)
            event.train.solution.done = True
            self.go_to_section(from_section=section, to_section=None, at=event.time)
            self.update(train=event.train, state=state, time=event.time)
            return True
        return False

    def check_if_free(self, links, _links, event):
        if len(links) > 0:
            return False
        else:
            link = random.choice(_links)
            self.blocked_trains.add(link.train)
            # blocking_tains = set(link.block_by()).intersection(self.blocked_trains)
            blocking_tains = set(link.block_by())
            if self.is_late(event) and len(blocking_tains) > 0:
                _train = blocking_tains.pop()
                trains_pair = tuple(sorted((_train.int_id, event.train.int_id)))

                if trains_pair not in self.priorities:
                    b = [event.train, _train]
                    random.shuffle(b)
                    self.priorities[trains_pair] = b
                a = self.priorities[trains_pair]
                self.avoid(a[0], a[1], event)

            event.time += self.wait_time
            self.register_event(event)

            return True

    def check_earliest_entry(self, section, event):
        if section.get_requirement() is not None and section.get_requirement().get_entry_earliest() is not None and event.time < section.get_requirement().get_entry_earliest():
            event.time = section.get_requirement().get_entry_earliest()
            self.register_event(event)
            return True
        return False

    def check_connections(self, section, event):
        if section is not None and self.with_connections:
            r = section.get_requirement()
            if r is not None:
                for c in r.waiting_connections:
                    connecting_train = c.from_train
                    marker = c.from_section_marker
                    _s = None
                    for c_s in connecting_train.solution.sections:
                        if c_s.get_marker() == marker:
                            _s = c_s
                            break
                    if _s is None:
                        # conencting train did not yet arrived. Need to wait..
                        event.time += self.wait_time
                        self.register_event(event)
                        return True
                    else:
                        # connection train is or has been on the section, check min time
                        should_wait = event.time - _s.entry_time < c.min_connection_time
                        if should_wait:
                            event.time += self.wait_time
                            self.register_event(event)
                            return True
        return False

    def remove_link_to_avoid(self, links, train):
        _links = []
        trains_are_on = [t.solution.sections[-1].section for t in train.other_trains if len(t.solution.sections) > 0]
        for link in links:
            if self.qtable.can_go(on=link, if_are_on=trains_are_on):
                _links.append(link)
        return _links

    def avoid(self, train1, train2, event):
        blocking_link = train2.solution.sections[-1]
        bb = train2.solution.other_trains_sections[-1]
        if train1 not in bb:
            return
        if_on = bb[train1]
        back_time = blocking_link.entry_time - 1 #- random.randint(1, 30 * 60)

        self.qtable.do_not_go(on=blocking_link.section, if_on=if_on.section)

        n1, n2 = len(self.trains), len([t for t in self.trains if t.solution.done])

        logging.info("%s (%i/%i) \tDO NOT ENTER %s IF ON %s going back to %s " % (
            humanize_time(event.time), n2, n1, blocking_link, if_on, humanize_time(back_time)))

        raise BlockinException(back_time=back_time, n=n2)

    def assign_limit(self):
        for train in self.trains:
            distances = dijkstra(source="start", dest="end", train=train)

            l = list(train.network.nodes["end"].in_links)[0]
            r = l.get_requirement()
            for n in train.network.nodes.values():
                n.limit = r.get_exit_latest() - (distances["end"] - distances[n.label])

    def free_all_resources(self):
        for r in self.resources.values():
            r.free = True
            r.currently_used_by = None
            r.last_exit_time = None
            r.last_used_by = None

    def update(self, train, state, time):
        if len(train.solution.sections) > 1:
            p_state = train.solution.states[-1]
            last_action = train.solution.sections[-1]

            reward = 10.0 - last_action.calc_penalty()
            self.qtable.update_table(p_state, current_state=state, previous_action=last_action, reward=reward)

    def go_to_section(self, from_section, to_section, at):
        train = from_section.train
        to_resources = []

        if to_section is not None:
            to_resources = [r for r in to_section.get_resources()]
            to_section.entry_time = at

        # release previous section
        if from_section is not None:
            from_section.exit_time = at
            from_resources = set(from_section.get_resources())
            to_resources = set(to_resources)
            for from_r in from_resources.difference(to_resources):
                release_at = at + from_r.get_release_time()
                from_r.exit(train=train, at=at)

                next_event = ReleaseResourceEvent(train=train, time=release_at, emited_at=at, resource=from_r)
                self.register_event(next_event)

        # block next section
        for to_r in to_resources:
            to_r.enter(train=to_section.train, at=at)

        if to_section is not None:
            self.register_event(self.next_event_for_train(to_section=to_section, at=at))

    def next_event_for_train(self, to_section, at):
        train = to_section.train
        # register next event: EnterNode or EnterStation
        requirement = to_section.get_requirement()
        next_time = to_section.get_minimum_running_time() + at
        if isinstance(requirement, HaltRequirement):
            earliest_entry = to_section.get_requirement().get_entry_earliest()
            # this test should be done before
            time = max(earliest_entry, next_time)
            return EnterStationEvent(time=time, section=to_section, train=train)
        else:
            return EnterNodeEvent(time=next_time, train=train, node=to_section.get_end_node(),
                                  previous_section=to_section)

    def register_event(self, event):
        assert event.time != np.inf
        assert event.time < 18 * 60 * 60
        event.time = max(event.time, self.current_time + 1)
        assert not np.isnan(self.current_time)
        assert not np.isnan(event.time)

        assert self.current_time < event.time, "current time = %s, event.time = %s " % (
            humanize_time(self.current_time), humanize_time(event.time))
        self.min_time = min(self.min_time, event.time)
        self.max_time = max(self.max_time, event.time)
        self.events[event.time].append(event)

    def get_train(self, name):
        for train in self.trains:
            if str(train.get_id()) == str(name):
                return train

    def go_back(self, time):
        self.blocked_trains = set()
        self.min_time = 9999999
        self.max_time = 0

        self.free_all_resources()

        self.events = defaultdict(list)
        self.current_time = time

        assert time < np.inf

        # reset solutions for all trains
        for train in self.trains:
            solution = train.solution

            _sections = []
            _states = []
            _other_trains_sections = []

            for section, state, trains_sections in zip(solution.sections, solution.states,
                                                       solution.other_trains_sections):
                if section.entry_time <= time:
                    _sections.append(section)
                    _states.append(state)
                    _other_trains_sections.append(trains_sections)

            n = len(_sections)
            for i, section in enumerate(_sections):
                on_last_current_section = i == n - 1
                if on_last_current_section:
                    continue

                resources = set(section.get_resources())
                if not on_last_current_section:
                    next_section = _sections[i + 1]
                    next_resources = set(next_section.get_resources())
                    resources = resources.difference(next_resources)

                for r in resources:
                    assert section.exit_time != np.inf
                    release_at = section.exit_time + r.get_release_time()
                    if release_at > time:
                        assert release_at < 25 * 60 * 60
                        next_event = ReleaseResourceEvent(train=train, time=release_at, emited_at=section.exit_time,
                                                          resource=r)
                        self.register_event(next_event)
                        r.enter(train=train, at=section.entry_time)
                        r.exit(train=train, at=section.exit_time)

            if len(_sections) > 0:
                last_section = _sections[-1]

                if last_section.exit_time >= time:
                    last_section.exit_time = np.inf
                    assert last_section.entry_time < np.inf
                    event = self.next_event_for_train(to_section=last_section, at=last_section.entry_time)
                    event.time = max(time, event.time)
                    assert event.time < 18 * 60 * 60
                    self.register_event(event)
                    for r in last_section.get_resources():
                        r.enter(train, at=last_section.entry_time)
                else:
                    assert last_section.get_end_node().label == "end"

                    for r in last_section.get_resources():
                        assert last_section.exit_time != np.inf
                        release_at = last_section.exit_time + r.get_release_time()
                        if release_at > time:
                            assert release_at < 25 * 60 * 60
                            next_event = ReleaseResourceEvent(train=train, time=release_at,
                                                              emited_at=last_section.exit_time, resource=r)
                            self.register_event(next_event)
                            r.enter(train=train, at=last_section.entry_time)
                            r.exit(train=train, at=last_section.exit_time)

            else:
                event = train.get_start_event()
                self.register_event(event)

            # train.solution = Solution(train=train)

            train.solution.sections = _sections
            train.solution.states = _states
            train.solution.other_trains_sections = _other_trains_sections
