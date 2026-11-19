#!/bin/bash
# Always-on experiment worker for a cloud VM (e.g. Google Cloud, 8 vCPUs).
#
# Polls GitHub for branches named gcp-exp/<name> that contain
# notes/exp/plan.json (same format as the Actions workflow) and no
# notes/results/<exp>/SUMMARY.md yet. For each, it builds both engines from
# that branch, plays every run of the plan on all cores, commits the results
# and SUMMARY.md, and pushes them back to the branch.
#
# One-time VM setup (Debian/Ubuntu):
#   sudo apt-get update && sudo apt-get install -y git build-essential python3-venv curl
#   ssh-keygen -t ed25519 -N "" -f ~/.ssh/smother_deploy
#   # Add ~/.ssh/smother_deploy.pub as a deploy key WITH write access in the
#   # repo's Settings > Deploy keys (paste it there yourself, not in any chat).
#   printf 'Host github.com\n  IdentityFile ~/.ssh/smother_deploy\n' >> ~/.ssh/config
#   git clone git@github.com:Demonic1594/Smotherfish.git ~/smotherfish
#   nohup bash ~/smotherfish/notes/scripts/gcp_worker.sh > ~/worker.log 2>&1 &
set -u
REPO=${REPO:-$HOME/smotherfish}
W=${W:-$HOME/work}
POLL=${POLL:-120}
OPPONENT_COMMIT=edb0d9db6731067ec50ce619ff372b463bc4dd5d
ARCH=${ARCH:-x86-64-avx2}
CONC=${CONC:-$(nproc)}
mkdir -p "$W"
[ -x "$W/venv/bin/python" ] || { python3 -m venv "$W/venv" && "$W/venv/bin/pip" -q install chess; }

build() {  # build ours from the checked-out branch; the opponent once
  (cd src && make -j"$CONC" net >/dev/null 2>&1 && make -j"$CONC" build ARCH=$ARCH >/dev/null 2>&1) || return 1
  cp src/stockfish "$W/ours"
  if [ ! -x "$W/opp" ]; then
    git fetch -q --depth 1 origin $OPPONENT_COMMIT || return 1
    rm -rf "$W/oppsrc" && mkdir -p "$W/oppsrc"
    git archive $OPPONENT_COMMIT src scripts | tar -x -C "$W/oppsrc"
    cp src/nn-*.nnue "$W/oppsrc/src/"
    (cd "$W/oppsrc/src" && make -j"$CONC" build ARCH=$ARCH >/dev/null 2>&1) || return 1
    cp "$W/oppsrc/src/stockfish" "$W/opp"
  fi
}

run_plan() {
  local exp jobs
  exp=$(python3 notes/scripts/expand_plan.py notes/exp/plan.json | sed -n 's/^exp=//p')
  jobs=$(python3 notes/scripts/expand_plan.py notes/exp/plan.json | sed -n 's/^matrix=//p')
  mkdir -p "notes/results/$exp"
  # One chunk at a time, each using every core.
  echo "$jobs" | python3 -c 'import json,sys
for j in json.load(sys.stdin): print(j["name"], j["elo"], j["games"], j["seed"], j["tc"], j["opts"])' |
  while read -r name elo games seed tc opts; do
    args=(); for o in $opts; do args+=(--opt "$o"); done
    "$W/venv/bin/python" -I notes/scripts/match.py "notes/results/$exp/$name.jsonl" \
      "$W/ours" "$W/opp" "$elo" "$games" --seed "$seed" --conc "$CONC" --tc "$tc" \
      --book notes/openings.txt "${args[@]}" | tail -1
  done
  { echo '```'; "$W/venv/bin/python" -I notes/scripts/summary.py notes/results/$exp/*.jsonl; echo '```'; } \
    > "notes/results/$exp/SUMMARY.md"
  git add "notes/results/$exp" && git commit -q -m "results: $exp (gcp worker)" && git push -q
}

cd "$REPO" || exit 1
while true; do
  git fetch -q --prune origin '+refs/heads/gcp-exp/*:refs/remotes/origin/gcp-exp/*' 2>/dev/null
  for ref in $(git for-each-ref --format='%(refname:short)' refs/remotes/origin/gcp-exp/); do
    branch=${ref#origin/}
    git show "$ref:notes/exp/plan.json" >/dev/null 2>&1 || continue
    exp=$(git show "$ref:notes/exp/plan.json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["exp"])')
    git show "$ref:notes/results/$exp/SUMMARY.md" >/dev/null 2>&1 && continue  # already done
    echo "$(date -u +%FT%TZ) running $branch ($exp)"
    git checkout -q -B "$branch" "$ref" && git branch -q -u "$ref" && build && run_plan \
      && echo "$(date -u +%FT%TZ) done $branch" || echo "$(date -u +%FT%TZ) FAILED $branch"
  done
  sleep "$POLL"
done
