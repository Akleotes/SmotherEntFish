#!/usr/bin/env python3
"""Merge the results of one experiment split over several accounts.

usage: merge_shards.py EXP OUTDIR REPO_URL[@BRANCH]...

Fetches notes/results/EXP/*.jsonl from each REPO_URL's branch (default
actions-exp/EXP), concatenates the files of the same name into OUTDIR and
prints how many games each shard contributed. Then run summary.py on OUTDIR.
"""
import os, subprocess, sys, tempfile

exp, out, srcs = sys.argv[1], sys.argv[2], sys.argv[3:]
os.makedirs(out, exist_ok=True)
merged = {}
for src in srcs:
    url, _, br = src.partition("@")
    br = br or f"actions-exp/{exp}"
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["git", "init", "-q", d], check=True)
        r = subprocess.run(["git", "-C", d, "fetch", "-q", "--depth", "1", url, br])
        if r.returncode:
            print(f"{src}: not available"); continue
        names = subprocess.run(["git", "-C", d, "ls-tree", "--name-only", "FETCH_HEAD", f"notes/results/{exp}/"],
                               capture_output=True, text=True).stdout.split()
        n = 0
        for f in names:
            if not f.endswith(".jsonl"):
                continue
            data = subprocess.run(["git", "-C", d, "show", f"FETCH_HEAD:{f}"], capture_output=True, text=True).stdout
            merged.setdefault(os.path.basename(f), []).append(data)
            n += data.count("\n")
        print(f"{src}: {n} games")
for name, parts in merged.items():
    with open(os.path.join(out, name), "w") as fh:
        fh.write("".join(p if p.endswith("\n") or not p else p + "\n" for p in parts))
print(f"merged {len(merged)} files into {out}")
