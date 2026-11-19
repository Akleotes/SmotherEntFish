#!/usr/bin/env python3
"""Expand an experiment plan into a GitHub Actions matrix.

plan.json:
  {"exp": "exp4", "tc": "5+0.05", "chunk": 100,
   "runs": [{"name": "base_e1500", "elo": 1500, "games": 400, "seed": 10,
             "opts": ["SmotherShape=32", "SmotherShapeAlways=true"]}]}

Each run is split into chunks of `chunk` games (even), one matrix job per
chunk, with seed = run seed + chunk index so chunks use different openings.
Prints `exp=...` and `matrix=...` lines for $GITHUB_OUTPUT.
"""
import json, sys

plan = json.load(open(sys.argv[1]))
default_chunk = int(plan.get("chunk", 100))
tc = plan.get("tc", "5+0.05")
jobs = []
for run in plan["runs"]:
    chunk = int(run.get("chunk", default_chunk))
    chunk -= chunk % 2
    games, i = int(run["games"]), 0
    while games > 0:
        g = min(chunk, games)
        g -= g % 2
        if g <= 0:
            break
        jobs.append({"name": run["name"], "elo": int(run["elo"]), "games": g,
                     "seed": int(run.get("seed", 1)) + i, "chunk": i,
                     "opts": " ".join(run.get("opts", [])), "tc": run.get("tc", tc)})
        games -= g
        i += 1
if len(jobs) > 256:
    sys.exit("matrix too large (max 256 jobs)")
print("exp=" + plan["exp"])
print("matrix=" + json.dumps(jobs))
