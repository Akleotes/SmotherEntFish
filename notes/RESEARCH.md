# Research notes: smother-oriented engines, books, opponent modelling

- No engine, Stockfish fork or opening book targets smothered mates
  (GitHub/web search, Nov 2026). Style forks target attack in general:
  ShashChess (Tal/Capablanca/Petrosian by eval), Kayra Attack, Patricia
  (net retrained on filtered "aggressive" positions), Rodent IV
  (hand-tuned king-attack personalities).
- No smother-trap Polyglot book exists. Known smother traps are teaching
  lines, e.g. Caro-Kann 1.e4 c6 2.d4 d5 3.Nc3 dxe4 4.Nxe4 Nd7 5.Qe2 Ngf6?? 6.Nd6#.
- Lichess puzzle DB (CC0, ~6M puzzles) has a `smotheredMate` theme: a large
  test set for the prover.
- Opponent-model search (Carmel & Markovitch 1996; Donkers 2003, probabilistic
  OM search): choose moves that exploit a known opponent model; dangerous if
  the model is wrong.
- Lc0 WDL contempt / WDLCalibrationElo: riskier play against weaker opponents.
- Stockfish 19 weak play (src/search.cpp Skill::pick_best): level =
  cubic(e), e=(Elo-1320)/1870; the move is picked from MultiPV 4 at depth
  1+level with push = (weakness*(top-score) + delta*rand%weakness)/128,
  weakness = 120-2*level. Picking depth: Elo 1500 ~2-3, 2000 ~5, 2500 ~8,
  3000 ~15. So short traps work only at low Elo; at 3000 smothers must come
  from converting won positions.

## Aesthetic mate selection (Nov 20, with an outside review)

- No Stockfish fork or other engine found that prefers a mating pattern
  over the shortest mate. Smotherfish already does this (a proven smother
  overrides; in brutal mode a plain mate scores below any smothered mate).
- CHESTHETICA (Azlan Iqbal): composes problems and can choose the most
  aesthetic winning line; aesthetics model in Iqbal's papers (WSEAS 2008,
  2012). No public source code found; a composition system, not a player.
  Choosing among forced mates does not create smother chances, which is
  the measured bottleneck here (proofs in ~2-3% of games).
- Mate finders (e.g. jhellis3's MateFinder fork, vondele/matetrack) aim at
  the shortest mate; nothing to borrow for smothers.
- Talkchess "Checkmate evaluation functions": reward progress toward the
  goal and the full reward only on delivery. Construction mode
  (SmotherBuild) is that idea applied to the corner smother.
- Outside review suggestions, status: blocker survivability (built, grid10);
  several target patterns instead of one corner pattern (later); escape
  prediction only on the opponent's time (later); full backward search from
  smother patterns (too expensive).
