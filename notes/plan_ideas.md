# Plan: more true smothers (Nov 22, 2026)

Ideas from three outside reviews (ChatGPT, DeepSeek, GLM; brief in
notes/review_brief.md) merged with our own queue. Already tested and dropped:
blocker survivability (grid10/12), prover time, escape budget, starve guard,
steering at all times, earlier construction.

## Phase 0: measure where smothers are lost (first)

- Failure causes per won game without a true smother.
- Opportunity recall (GLM): replay won games; in every position of ours with
  a winning eval, run the prover with a large budget ("oracle"). Classes:
  - never available: no forced smother in any winning position (supply);
  - available, never proven by the engine in the game (detection);
  - proven by the engine, not delivered (conversion).
  Script: notes/scripts/recall.py.

The split decides the order of phases 1 and 2: mostly missed or not
converted -> search control first; mostly never available -> eval first.

## Phase 1: search control in construction mode (all three reviews)

Each an option, off by default, active only in construction mode:
- less reduction / an extension for quiet moves that tighten the box or
  bring the knight closer to a mating square;
- an extension for defender moves that open a flight square (counterweight,
  against over-optimism);
- a smother history table for ordering (bonus along proven lines);
- no null move when the box is tight (zugzwang-prone positions).

## Phase 2: eval additions in the build score

- luft denial: penalise the defender's safe pawn moves that open a flight
  square, reward our control of those squares (GLM);
- knight route safety: knight distance weighted by danger on the route and
  on the landing square (ChatGPT, GLM);
- keep our own queen and mating knight (no trades in construction mode);
- hold back optional captures of box pieces (queued idea b);
- role-based keep weights (box pieces count, others not).

## Phase 3 (only if 1-2 stall)

- trap bonus: smothers sound only against imperfect defence, inside
  construction mode (GLM; our earlier steering at all times lost strength);
- a small learned "smother likely" model from our own games.

## Not doing (reasons)

Separate smother score band (risk of false mate scores), NNUE fine-tune
(strength risk, cost), static mate-at-a-glance (search and prover already
see it), proof-number search (prover time is not the bottleneck), prover
results in the TT (the proven line is already played), opening book
(changes play from move 1), smother endgame table (narrow, weeks of work),
dynamic near-smother switch (near, not true smothers).
