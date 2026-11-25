# Brief for outside review, round 3 (paste everything below)

You are reviewing a research project. Read all of it before answering.
Everything below is measured fact unless marked as a hypothesis. Do not
assume facts that are not written here; if an idea depends on one, say so
and say how we could measure it. Be concrete and critical; say so if you
think an idea of ours is a dead end.

## 1. The project

Smotherfish is a fork of the Stockfish chess engine (C++, NNUE, Stockfish
development version of Nov 2026). Goal: end as many games as possible with
a smothered mate, without losing playing strength. Current release 1.5.1.

Definition (the only one that counts now): a smothered mate is a mate
given by a KNIGHT against a king whose every neighbour square holds one of
its own pieces (the textbook "classic" smother). Queen mates against a
boxed king, and "near" smothers (one neighbour square empty but covered),
no longer count.

Two goals for the next version (1.6):
A. A large jump in knight smothers per 100 games.
B. Some real playing strength gained from Smotherfish's OWN machinery
   (prover, construction mode, smother knowledge), not from tuning
   Stockfish's search or evaluation (Stockfish's own tuning infrastructure
   is far beyond ours). Target was +5 Elo; see section 6 for what we have.

## 2. How the engine works

- Prover: an AND/OR proof search on a helper thread, parallel to the
  normal search. Attacker: checks (incl. sacrifices) plus 1-2 quiet moves
  that threaten a smother; defender: every legal reply. Iterative deepening
  to 8 attacker moves (12-16 when crushing), node and time limits. A proof
  replaces the search's move. Verified on all 24,506 Lichess
  "smotheredMate" puzzles. In real human games it proves 99% of the forced
  smothers that occurred.
- Construction mode: when our previous score >= +8 pawns (stay while >=
  +6), the static eval at every node of the normal search becomes, from
  our side: u = 600 + (u - 600)/8 + build_score * 8 cp (above 600 cp).
  A plain mate is scored only +600 cp so the search keeps building; a
  smothered mate keeps its true mate score. Up to 160 construction moves
  per game, then normal mating.
- build_score: hand-written terms (enemy pieces on the king ring, open
  ring squares, corner/edge, keep enemy pieces alive, escape squares,
  piece nearness) plus, for knight smothers, "KnightCheck": W points for a
  knight of ours one knight move from a square that checks the enemy king
  and that no enemy pawn guards (W/2 for two moves).
- SmotherClassic=true: only knight smothers are accepted as targets by the
  prover and the search.
- Against humans (detected via UCI_Opponent from lichess-bot), the engine
  stops building after 40 moves (humans resign lost positions; measured
  from 33M Lichess games).

## 3. Test setup

Python harness, real clocks, games played to mate / draw rules, no
adjudication, no resignation (except an optional measured Lichess blitz
resignation curve). 300 fixed openings x2 colours. Opponents: Stockfish
with UCI_Elo 1500 / 2500, and Maia-3 1500 (human-like net, sampled
moves). Mostly 5s+0.05s, one thread. Capacity: ~8 x 20 parallel jobs;
~14,000 games take ~1-2 hours. Strength via SPRT (paired games, 10s+0.1s).

## 4. Knight-smother results (per 100 games, nearly all games won)

vs Stockfish 1500 (2,500 games per arm unless noted):
- 1.5 default (aims at any-piece smothers): 0.7
- SmotherClassic + KnightCheck 8: 4.0
- KnightCheck 4 .. 24: plateau around 3-4
- + decoy term + prover limits (CrushQuiet 3, CrushMoves 16): +20-30%
  (not significant alone)
- Learned linear model (17 features, below) instead of the hand terms:
  scale 6 / 11 / 20 points per log-odd: 2.5 / 3.4 / 4.1 vs hand 3.8
  (higher scale better; 20 only matches the hand score)
vs Maia-3 1500 (600 games): similar, 2.5-4.3. vs Stockfish 2500 (400):
1.0-2.3. At 3+2: Stockfish 1500 3.7 vs 0.9 (1.5); Maia-3 6.3 vs 1.4.
No draws or losses to speak of (1 loss in 14,000 games).

Strength: SmotherClassic + KnightCheck 16 vs 1.5.1: +0.7 Elo (95% -0.5
to +1.8). Turning the prover off outside won positions: +0.3 Elo (95%
-0.6 to +1.2), i.e. the prover costs nothing measurable.

## 5. What the data says about knight smothers

- State analysis of our games: the bottleneck is the LAST open ring
  square. With the box closed, king in a corner, and our knight one move
  from a checking square, 82% end in a knight smother within 10 moves.
  Most construction time is spent with 1-2 open squares that never close.
- Logistic model on 17 hand features (corner, edge, 0/1/2 open squares,
  knight distance to a checking square, decoy pattern, queen present,
  king stuck, enemy piece count, defender "exits", our knights; plus
  interactions): AUC 0.936 for "knight smother within 10 of our moves";
  all pairwise products 0.947; more data does not help it.
- Small network (just built): the 17 features + a 5x5 window around the
  enemy king (mirrored to one corner; 6 channels per square: off-board,
  their pawn, their piece, our knight, our queen, our other) -> 16 ReLU ->
  logit. 4.56M positions, 13,390 positives, holdout by game: AUC 0.968
  (32 or 64 hidden: no better). In the engine it replaces the hand
  build_score terms (being tested now at several scales).
- Human data (33M Lichess games): knight smothers 0.68 per 1000 games;
  most are unforced blunders, not forced lines. Human "trap" moves did
  not help us (tested).

## 6. Already tried, no gain (do not re-propose without a new reason)

More prover time; escape budget; starve guard; steering by MultiPV trap
counts (lost strength); earlier construction (more draws); lower
construction floor; blocker survivability terms; robust/strict proofs;
LMR/null-move changes in construction mode; extra eval terms (own pieces
kept, enemy pieces near king, knight safety); "Keep" and "Starve" variants
for knight smothers; holding out for full smothers (NearHold); trap moves
learned from humans; turning the prover off in undecided positions (no
strength change).

## 7. Constraints

- No strength loss (SPRT before any default change). Bullet to blitz,
  single thread, also Android. No Stockfish search/eval tuning as the
  source of gains.
- Humans resign: at 8+ pawns down in blitz, 43% resign, 23% get mated,
  28% lose on time. Long construction loses games to resignation.
- Draws (50-move rule, repetition) in won positions are a real cost.

## 8. What I want from you

1. Knight smothers: what would at least DOUBLE knight smothers per 100
   games beyond ~4 (vs Stockfish 1500)? We think the last-open-square
   bottleneck is the key. Give up to 6 concrete ideas, ranked by expected
   gain x chance of working: mechanism, where it goes (root decision,
   eval at all nodes, prover, move ordering, time), cost, risk, and a test
   design with our setup.
2. The network: how should a learned predictor be USED in search to turn
   prediction into more smothers (score shaping, root-only steering,
   policy over moves, target selection, on-policy retraining, RL)? What
   are the failure modes (the search exploiting the net, etc.)?
3. Strength from our own machinery: is there any credible way the prover
   or smother knowledge can add measurable Elo (for example mate finding
   the main search misses, time use, pruning safety)? If you think it is
   not realistic, say so plainly and why.
