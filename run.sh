#!/bin/bash
source /Users/denism/work/train-schedule-optimisation-challenge-starter-kit/ENV/bin/activate

N_CORES=4
RANDOM=13443341

NO="07"
WAIT=10
MAX_DELTA=0
MIN_DELTA=0
N_STATE=1

for i in `seq 1 $N_CORES`;
do
	python main.py --no=$NO --wait=$WAIT --max_delta=$MAX_DELTA --min_delta=$MIN_DELTA --n_state=$N_STATE --epsilon=0.9 --alpha=0.8 --gamma=0.8 --seed=$i &
done
wait
