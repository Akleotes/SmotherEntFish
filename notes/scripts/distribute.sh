#!/usr/bin/env bash
# Spread one experiment over our account and every helper fork (default for
# all tests: faster results). Each target gets the plan with "shard": [i, n].
#
# usage: notes/scripts/distribute.sh PLAN.json [SRC_REF]
#   PLAN.json  experiment plan (notes/exp/plan.json format, "exp" = name)
#   SRC_REF    branch/commit whose src/ is tested (default: current branch)
#
# Branches are built on each fork's own default-branch version (the fork's
# token cannot push workflow changes), with src/ from SRC_REF and the plan.
# Helper forks pick them up on their poll (about hourly, or "Run workflow"
# on Actions > Helper poll); our shard starts on push.
set -euo pipefail
plan=$1; src=${2:-$(git rev-parse --abbrev-ref HEAD)}
# id:base (base = the version the fork is on; update after a "Sync fork")
targets=(
  "8e9ce5:33bbe361"
  "acf111:33bbe361"
  "7a213a:33bbe361"
  "0f17ee:33bbe361"
  "dc665d:33bbe361"   # no working schedule: Run workflow by hand
  "d32e35:33bbe361"   # enterprise account: limit 360, ramping up until ~Nov 29
                      # (about 20 jobs at once on Nov 23); its poll can be
                      # dispatched from the session
  "own:33bbe361"     # this repository
)
n=${#targets[@]}
exp=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["exp"])' "$plan")
tmp=$(mktemp); cp "$plan" "$tmp"
cur=$(git rev-parse --abbrev-ref HEAD)
git fetch -q origin smotherfish
for i in "${!targets[@]}"; do
  id=${targets[$i]%%:*}; base=${targets[$i]#*:}
  git checkout -q -B tmp-dist "$base"
  git checkout -q "$src" -- src
  mkdir -p notes/exp
  python3 - "$tmp" "$i" "$n" > notes/exp/plan.json <<'EOF'
import json, sys
p = json.load(open(sys.argv[1])); p["shard"] = [int(sys.argv[2]), int(sys.argv[3])]
p.setdefault("max_parallel", 20)  # a free account's full 20 (all forks synced)
print(json.dumps(p, indent=1))
EOF
  git add src notes/exp/plan.json
  git commit -q -m "$exp: shard $i/$n" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01AXQtdwTBPTjdbfRvbZua89"
  if [ "$id" = own ]; then ref=actions-exp/$exp; else ref=helper-exp/$id/$exp; fi
  git push -q -f origin tmp-dist:refs/heads/$ref
  echo "$ref: shard $i/$n (base $base)"
done
git checkout -q "$cur"; git branch -D -q tmp-dist; rm -f "$tmp"
echo "merge when done: notes/scripts/merge_shards.py $exp OUTDIR <fork URLs>@actions-exp/$exp"
