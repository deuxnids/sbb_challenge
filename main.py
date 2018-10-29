import logging
import sys
import glob
import os
import json
import random

sys.path.append(r"/Users/denism/work/sbb_challenge")
sys.path.append(r"/Users/denism/work/sbb_challenge/utils")

from simulator.simulator import Simulator
from simulator.simulator import BlockinException
from simulator.qtable import QTable
from simulator.event import humanize_time
import numpy as np

logger = logging.getLogger()
logger.setLevel(logging.INFO)

FORMAT = "[%(asctime)s %(filename)s:%(lineno)s - %(funcName)s ] %(message)s"
logging.basicConfig(format=FORMAT)

no = "05"
path = glob.glob(r"/Users/denism/work/train-schedule-optimisation-challenge-starter-kit/problem_instances/" + no + "*")[
    0]

qtable = QTable()

sim = Simulator(path=path, qtable=qtable)
sim.trains = sim.trains
sim.assign_limit()

i = 1

"""
1:
2:
3:
4:
5:
6: backward, mulit ->523, 499, 412, 456, 410, 387 (wait_time=30)
7:
8:
9: 
"""

sim.wait_time = 60
sim.max_delta = 10 * 60
sim.n_state = 0

# dijkstra or ..
sim.late_on_node = False
sim.with_connections = True
sim.backward = True

qtable.epsilon = 0.2
qtable.alpha = 0.8  # learning rate
qtable.gamma = 0.8  # discount factor

sim.initialize()
sim.assign_sections_to_resources()
sim.match_trains()
sim.spiegel_anschlusse()

score = 800
random.seed(2018)

logging.info("problem %s" % path)
logging.info("with backward %s" % sim.backward)
kk = 1
sub_tour = 100000
while i < 200:
    sim.initialize()
    sim.free_all_resources()
    i += 1
    j = 1
    while not sim.done and j < sub_tour:
        try:
            if not sim.backward:
                sim.initialize()
                sim.free_all_resources()
            j += 1
            sim.run()
        except BlockinException as e:

            n, n2 = len(sim.trains), len([t for t in sim.trains if t.solution.done])
            # logging.info("%s: %i/%i trains" % (humanize_time(sim.current_time), n2, n))
            if sim.backward:
                sim.go_back(e.back_time)
    if j == sub_tour:
        logging.info("resetting")
    if sim.compute_score() < score:
        break

folder = r"/Users/denism/work/train-schedule-optimisation-challenge-starter-kit/solutions"
output_path = os.path.join(folder, sim.timetable.label + "_for_submission.json")
with open(output_path, 'w') as outfile:
    json.dump([sim.create_output()], outfile)
