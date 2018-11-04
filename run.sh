#!/bin/bash
source /Users/denism/work/train-schedule-optimisation-challenge-starter-kit/ENV/bin/activate

N_CORES=4
RANDOM=1341


for i in `seq 1 $N_CORES`;
do
	python main.py --no="04" --wait=10 --max_delta=900 --min_delta=60 --n_state=5 --epsilon=0.2 --alpha=0.8 --gamma=0.8 --seed=$RANDOM &
done
wait
