import logging
import sys
import numpy as np
import glob
import os
import json
import random
import time
import argparse
from collections import defaultdict

#sys.path.append(r"/Users/denism/work/sbb_challenge")
#sys.path.append(r"/Users/denism/work/sbb_challenge/utils")

from simulator.simulator import Simulator
from simulator.simulator import BlockinException
from simulator.qtable import QTable

logger = logging.getLogger()
logger.setLevel(logging.INFO)

FORMAT = "[%(asctime)s %(filename)s:%(lineno)s - %(funcName)s ] %(message)s"
logging.basicConfig(format=FORMAT)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--no", default="06")
    parser.add_argument("--wait", default=10, type=int)
    parser.add_argument("--max_delta", default=60, type=int)
    parser.add_argument("--min_delta", default=60, type=int)
    parser.add_argument("--n_state", default=1, type=int)
    parser.add_argument("--epsilon", default=0.1, type=float)
    parser.add_argument("--alpha", default=0.8, type=float)
    parser.add_argument("--gamma", default=0.8, type=float)
    parser.add_argument("--seed", default=2018, type=int)

    args = parser.parse_args()
    no = args.no

    #path = glob.glob(r"/Users/denism/work/train-schedule-optimisation-challenge-starter-kit/problem_instances/" + no + "*")[0]
    path = glob.glob(r"inputs/" + no + "*")[0]

    qtable = QTable()

    sim = Simulator(path=path, qtable=qtable)
    sim.trains = sim.trains
    sim.assign_limit()

    sim.wait_time = args.wait
    sim.max_delta = args.max_delta
    sim.min_delta = args.min_delta
    sim.n_state = args.n_state

    # dijkstra or ..
    sim.late_on_node = False
    sim.with_connections = True
    sim.backward = True

    qtable.epsilon = args.epsilon
    qtable.alpha = args.alpha  # learning rate
    qtable.gamma = args.gamma  # discount factor

    sim.initialize()
    sim.assign_sections_to_resources()
    sim.spiegel_anschlusse()
    sim.match_trains()

    score = np.inf
    random.seed(args.seed)

    logging.info("problem %s" % path)
    logging.info("with backward %s" % sim.backward)

    start_time = time.time()

    folder = r"outputs/"
    output_folder = os.path.join(folder, sim.timetable.label.replace("/", "_"))
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    i = 1
    sub_tour = 1000000
    while i < 200:
        sim.initialize()
        sim.free_all_resources()
        i += 1
        j = 1
        last_n = None
        #sim.qtable.to_avoid = defaultdict(list)
        while not sim.done and j < sub_tour:
            try:
                if (time.time()-start_time) > 2*15*60:
                    sys.exit()

                if not sim.backward:
                    sim.initialize()
                    sim.free_all_resources()
                sim.blocked_trains = set()
                sim.run()

                _score = sim.compute_score()
                if sim.compute_score() < score:
                    score = _score
                    output_path = os.path.join(output_folder, "%f.json" % score)
                    with open(output_path, 'w') as outfile:
                        json.dump([sim.create_output()], outfile)
                    if score == 0.0:
                        break

                sim.wait_time = max(1.0, sim.wait_time - 5)
            except BlockinException as e:

                #delays = [t.solution.get_delays() for t in sim.trains]
                #delays = [d for d in delays if d > 0.0]
                #logging.info(delays)
                if sim.backward:
                    sim.go_back(e.back_time)
        #            if last_n == e.n:
        #                j += 1
        #            else:
        #                j = 1
        #                last_n = e.n
        #if j == sub_tour:
            #logging.info("resetting")
            #sim.wait_time = max(1.0, sim.wait_time - 5)
            #logging.info(sim.wait_time)

