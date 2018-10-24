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

logger = logging.getLogger()
logger.setLevel(logging.INFO)

FORMAT = "[%(asctime)s %(filename)s:%(lineno)s - %(funcName)s ] %(message)s"
logging.basicConfig(format=FORMAT)

no = "05"
path = glob.glob(r"/Users/denism/work/train-schedule-optimisation-challenge-starter-kit/problem_instances/"+no+"*")[0]

qtable = QTable()

sim = Simulator(path=path, qtable=qtable)
sim.trains = sim.trains
sim.assign_limit()

i = 1

#with backward wait_time needs to be set on 1. Why? No idea...
sim.wait_time = 30
sim.max_delta = 15 * 60
sim.n_state = 0
sim.with_connections = True
sim.backward = True

qtable.epsilon = 0.2
qtable.alpha = 0.8  # learning rate
qtable.gamma = 0.8  # discount factor


sim.initialize()
sim.assign_sections_to_resources()
sim.match_trains()
sim.spiegel_anschlusse()

score = 200
random.seed(2018)

logging.info("proble %s" % path)
logging.info("with backward %s" % sim.backward)
j = 1

while i < 2:
    sim.initialize()
    sim.free_all_resources()
    i += 1
    while not sim.done:
        try:
            if not sim.backward:
                sim.initialize()
                sim.free_all_resources()
            j+=1
            sim.run()
        except BlockinException as e:
            n, n2 = len(sim.trains), len([t for t in sim.trains if t.solution.done])
            # logging.info("%s: %i/%i trains" % (humanize_time(sim.current_time), n2, n))
            if sim.backward:
                sim.go_back(e.back_time)
    sim.backward = True

folder = r"/Users/denism/work/train-schedule-optimisation-challenge-starter-kit/solutions"
output_path = os.path.join(folder, sim.timetable.label + "_for_submission.json")
with open(output_path, 'w') as outfile:
    json.dump([sim.create_output()], outfile)