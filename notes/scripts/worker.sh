#!/bin/bash
# Experiment worker: build engines, run matches, commit results.
# usage: notes/scripts/worker.sh EXP_NAME 'NAME ELO GAMES [--opt K=V ...]' ['...' ...]
# Run from the repo root on the experiment's branch. Results go to
# notes/results/EXP_NAME/NAME.jsonl and are committed (push is up to the caller).
set -e
EXP=$1; shift
ROOT=$(pwd); W=$ROOT/../work; mkdir -p $W
# Our engine
(cd src && make -j4 net >/dev/null 2>&1 && make -j4 build ARCH=x86-64-bmi2 >/dev/null 2>&1)
cp src/stockfish $W/ours
# Opponent: stock Stockfish 19 (commit edb0d9db is in this repo)
if [ ! -x $W/sf_stock ]; then
  rm -rf $W/sf19 && mkdir -p $W/sf19
  git archive edb0d9db src scripts | tar -x -C $W/sf19
  cp src/nn-*.nnue $W/sf19/src/
  (cd $W/sf19/src && make -j4 build ARCH=x86-64-bmi2 >/dev/null 2>&1)
  cp $W/sf19/src/stockfish $W/sf_stock
fi
[ -x $W/venv/bin/python ] || { python3 -m venv $W/venv && $W/venv/bin/pip -q install chess; }
mkdir -p notes/results/$EXP
for job in "$@"; do
  set -- $job; name=$1; elo=$2; games=$3; shift 3
  $W/venv/bin/python -I notes/scripts/match.py notes/results/$EXP/$name.jsonl $W/ours $W/sf_stock \
    $elo $games --book notes/openings.txt "$@" | tail -1
done
$W/venv/bin/python -I notes/scripts/summary.py notes/results/$EXP/*.jsonl
git add notes/results/$EXP && git commit -q -m "results: $EXP" && echo committed
