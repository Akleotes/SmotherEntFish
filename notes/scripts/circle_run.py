#!/usr/bin/env python3
"""Run this CircleCI machine's share of an experiment plan.

usage: circle_run.py PLAN.json NODE_INDEX NODE_TOTAL CONC

Expands the plan with expand_plan.py (the same matrix as the GitHub
workflow), takes every job whose position modulo NODE_TOTAL equals
NODE_INDEX, and plays it with match.py into out/<name>-<chunk>.jsonl.
Only Stockfish-at-UCI_Elo opponents are available here: jobs against
Maia ("maia-*") or a reference build ("ref") are skipped with a note.
CONC is given explicitly because nproc in a CircleCI Docker job reports
the host's CPUs, not the resource class's.
"""
import json, os, subprocess, sys

plan, node, total, conc = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
here = os.path.dirname(os.path.abspath(__file__))
out = subprocess.run([sys.executable, "-I", os.path.join(here, "expand_plan.py"), plan],
                     capture_output=True, text=True, check=True).stdout
matrix = json.loads(next(l for l in out.splitlines() if l.startswith("matrix="))[7:])
mine = [j for i, j in enumerate(matrix) if i % total == node]
print(f"node {node}/{total}: {len(mine)} of {len(matrix)} jobs", flush=True)
os.makedirs("out", exist_ok=True)
for j in mine:
    if j["opp"]:
        print(f"skip {j['name']} chunk {j['chunk']}: opponent {j['opp']} is not built here", flush=True)
        continue
    args = []
    for o in j["opts"].split():
        args += ["--opt", o]
    if j.get("ponder"):
        args.append("--ponder")
    args += ["--opp-think", str(j.get("think", 0))]
    cmd = [sys.executable, "-I", os.path.join(here, "match.py"),
           f"out/{j['name']}-{j['chunk']}.jsonl", "engines/ours", "engines/opp",
           str(j["elo"]), str(j["games"]), "--seed", str(j["seed"]), "--conc", str(conc),
           "--tc", j["tc"], "--book", "notes/openings.txt"] + args
    print("run", j["name"], "chunk", j["chunk"], flush=True)
    subprocess.run(cmd, check=False)
