# Brief for outside model review (paste everything below into the model)

I am working on Smotherfish, a fork of the Stockfish chess engine (C++, NNUE)
whose goal is to deliver smothered mates (a knight mates a king that is boxed in
by its own pieces) as often as possible WITHOUT losing playing strength. I want
new, concrete, testable ideas to raise the rate of TRUE (full) smothered mates.
Please think carefully and be specific about how each idea would be implemented
inside a Stockfish-style search.

## What exists now

- Smother prover: a separate search on a helper thread that proves forced
  smothered mates (attacker plays checks plus a limited number of quiet moves,
  defender plays all replies). A proven smother overrides the normal best move.
  It is verified on 2000 Lichess smother puzzles with no errors.
- Brutal mode (on by default): when clearly winning, the engine prefers
  delivering a smother over a faster ordinary mate, within time/plies budgets.
- Construction mode: once the eval is above a threshold (+8 pawns, with a
  +6 pawn floor that is never given up), the root move choice adds a
  "smother build score": enemy king boxed in by its own pieces, our knight
  routes to the mating squares, enemy pieces kept alive near their king
  ("keep" weight 8 per enemy piece). This was the one big breakthrough
  (true smothers went from about 1-2 to about 12 per 100 games vs Elo 1500).
- "Hybrid" goal: after 40 moves of construction without success it also
  accepts a "near" smother (all but one flight square blocked by own pieces).
- Strength: equal to unmodified Stockfish (43,200 games at 10+0.1:
  -0.3 Elo, 95% -1.1 to +0.4).

## Current results (per 100 games, all games won or nearly all)

- 3+2 vs Stockfish UCI_Elo 1500: 11.8 full smothers, 69 full-or-near.
- 3+2 vs Elo 2000: about 61 full-or-near; vs Elo 2500: about 46.
- 5+0.05 vs Elo 3000: about 1-2 full, 13 full-or-near.
- Vs Maia-3 (human-like net) 1100-2300: 8-13 full, 47-58 full-or-near.

## What we measured / already tried (please do not just repeat these)

- The bottleneck is ESCAPES: during construction the defender's king steps
  out, or the defender trades/captures blockers or our knight, so the box
  dissolves. Time/clock for the prover is NOT the bottleneck (tested).
- No gain: giving the prover more time, an "escape budget" (extra prover time
  after the opponent deviates), a starve guard (stop construction if no
  progress), several clock tweaks.
- Lost strength or drew more: steering among MultiPV moves by "number of
  smother traps set" at all times; starting construction earlier (lower eval
  threshold) - more draws, fewer smothers vs strong opponents.
- Helped: keeping enemy pieces alive (keep weight 3 -> 8), construction itself.
- Tested, inconclusive: blocker survivability in the build score (bonus for
  pinned / defended blockers, penalty if our knight can be won or a pawn
  blocker can step forward). 3000 games: "defended" 11.9 vs control 10.7
  full per 100 (p ~0.14); "pinned" and combinations no better.
- The prover already has: a proof table (transposition table, reused across
  sibling positions), iterative deepening mate-in-1..N, attacker move
  ordering (checks first, by distance to king) and defender ordering.
  Knight distance in the build score is a BFS in knight moves.
- Queued but untested: (b) hold back optional captures of pieces that help
  box the king;
  (c) predict opponent replies from our own game data; (d) forcing checks
  that drive defender pieces onto their own king's neighbourhood
  (for 2500-3000 opponents); (e) at 3000+, among near-equal moves choose
  smother-friendly ones.

## Constraints

- No measurable strength loss at full strength (we verify with SPRT).
- Must be cheap enough to run at blitz/bullet time controls (5+0.05 to 3+2).
- Single engine binary, also runs on Android phones.
- We have large test capacity (thousands of games per hour), so ideas only
  need to be testable, not proven in advance.

## What I want from you

1. Up to 8 ideas, ranked by (expected gain in TRUE smothers) x (chance it
   works without strength loss). For each: the mechanism, where in the search
   it goes, rough cost, and how to test it.
2. Your opinion on the queued ideas (b)-(e): which are worth it, which not.
3. One "long shot" idea that could double the rate if it worked.
4. Anything in our approach you think is a mistake.
