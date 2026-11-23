# Brief for outside model review, round 2 (paste everything below)

You are reviewing a research project. Read all of it before answering.
Everything below is measured fact unless marked as a hypothesis. Do not
assume anything that is not written here; if your idea depends on a fact
not given, say so explicitly and say how we could measure it.

## 1. The project

Smotherfish is a fork of the Stockfish chess engine (C++, NNUE evaluation,
Stockfish development version of 22 Nov 2026). Goal: end as many games as
possible with a smothered mate, WITHOUT losing playing strength.

Strength today (verified): equal to unmodified Stockfish. 43,200 games at
10s+0.1s: -0.3 Elo (95% -1.1 to +0.4). The latest version (1.3) vs the
previous one: +1.3 Elo (95% +0.2 to +2.4) over 21,600 games; at 60s+0.6s vs
Stockfish, +0.5 Elo (95% -0.6 to +1.7) over 7,320 games. Strength is
measured with SPRT runs; any default change must pass one.

## 2. Definitions (important: three kinds of smothered mate)

At checkmate, look at the squares next to the mated king:
- Classic (knight) smother: every neighbour square holds one of the mated
  side's own pieces. Only a knight can give this mate. This is the textbook
  "smothered mate".
- AnyPiece ("full") smother: every neighbour square holds one of the mated
  side's own pieces, EXCEPT the square of the checking piece itself (e.g. a
  queen giving check from an adjacent square, protected). Includes classic.
  This is what the engine and our test harness count as "full" by default
  (option SmotherClassic = false).
- Near ("all but one") smother: as AnyPiece but exactly one more neighbour
  square is empty or holds an attacker piece (it is covered by the attacker,
  since the position is mate).
- Plain mate: any other mate.

In our measurements, of 227 "full" smothers in 2,500 games, only 22 were
classic (knight) smothers; the rest were mostly queen mates against a fully
boxed king.

## 3. How the engine works (exact)

All of this is active only in "brutal mode" (option SmotherBrutal, on by
default). The bench signature is computed with it off.

### 3.1 The prover (src/smother.cpp)
- Exhaustive AND/OR proof search on a helper thread running in parallel to
  the normal search (SmotherParallel). Attacker may play any checking move
  (including sacrifices) plus at most SmotherQuietMoves quiet moves that
  threaten a smother; defender plays every legal reply.
- Iterative deepening up to SmotherMaxMoves attacker moves, with its own
  proof table, node limit (SmotherNodes 5,000,000) and time limit.
- Defaults: 8 moves, 1 quiet move. When "crushing" (previous score is a
  mate, or >= SmotherBigCp = +10.00 pawns, or construction mode is on):
  at least 12 moves and 2 quiet moves, and time = SmotherBrutalTimePercent
  (300%) of the move's optimum time, capped at 60% of the maximum.
- Proof rule (default, non-strict): the longest defence must end in a
  smothered mate; every other defence must lose to a strictly faster
  ordinary mate. Strict mode (SmotherStrict): every defence must be
  smothered. A line that repeats a position seen in the game or on the line
  is not a proof.
- When a proof is found, its first move replaces the normal search's move.
- Verified: all 24,506 Lichess puzzles with the "smotheredMate" theme.
- Hybrid near proofs: if a near proof is found, it also looks for a full
  smother at most SmotherFullExtra (3) moves longer and prefers it.

### 3.2 Construction mode (the main lever so far)
Decided once per move at the root, from the previous search's score:
- Enter when the previous score >= SmotherBuildCp (+8.00 pawns) or a forced
  mate; stay while >= SmotherBuildFloor (+6.00 pawns) or a mate.
- Only while: construction moves used this game < SmotherBuildMoves (80),
  50-move counter < 60 half-moves, and the enemy has >= 4 pieces (any kind,
  king included).
- While on, the static evaluation at EVERY node of the normal search (not
  only the root) is changed, from our side's view u:
  if u >= floor (600 cp): u = 600 + (u - 600)/8 + build_score * 8 cp.
  Below the floor: unchanged Stockfish eval.
- A plain (non-smother) mate found in the search is scored as only +600 cp
  (the floor), so the search keeps building instead of mating. A smothered
  mate keeps its real mate score.
- Search control (LMR, null move, pruning, extensions, history) is
  unchanged Stockfish.

build_score(position) in points (defaults; "ring" = the 3-8 squares next
to the enemy king; "theirs" = enemy non-king pieces including pawns):
  13 x (ring squares holding enemy pieces)
  - 8 x (ring squares not holding enemy pieces)
  + 23 if the enemy king is in a corner, else + 8 if on an edge
  + 11 x (number of enemy non-king pieces)        (SmotherBuildKeep)
  + 2 x (enemy non-king pieces within 2 squares of their king) (KeepNear)
  - 4 x (ring squares holding no enemy piece and not attacked by us) (Escape)
  + 2 x max(0, 4 - distance(our knight, enemy king)) per knight
  + 4 x max(0, 4 - distance(our queen, enemy king)) per queen
(distance = king-move distance). These weights were tuned on game results
(phase 3 below).

### 3.3 Goals: Full / Hybrid (default) / Near
- Full: only full smothers count (prover style AnyPiece).
- Hybrid (default): full only until 40 construction moves have been played
  this game (SmotherPartialAfter, default 40 under Hybrid); from then on the
  prover also accepts near smothers, and in the search a near smother
  counts as a real mate three moves later than a full one (so a full one up
  to 3 moves longer is preferred). A plain mate still counts only +600 cp.
- Near: near smothers count from the start.
- After SmotherBuildMoves (80) construction moves, construction ends and
  the engine mates normally (plain mate).

## 4. Test setup (exact)
- Our harness (Python, python-chess): real clocks, each game played to
  checkmate, stalemate, insufficient material, threefold repetition, the
  50-move rule, or a 400-ply cap. NO adjudication, NO resignation.
- Openings: 300 fixed positions (about 4-5 moves deep), each played twice
  with colours swapped; shuffled by seed.
- Opponents: Stockfish with UCI_LimitStrength (UCI_Elo 1500 / 2000 / 2500 /
  3000), same clock; or Maia-3 (a neural net trained to play like humans
  of a given rating), playing "go nodes 1" (instant, human-like moves).
- Time controls: mostly 5s + 0.05s per move (bullet; our clock is tight:
  measured median 0.24 s left at our move 30); also 3min + 2s.
- One CPU thread per engine. Results: full / classic / near per 100 games.
- Capacity: about 7 GitHub accounts x ~20 parallel jobs; a 7,000-game
  experiment at 5+0.05 takes about 30-60 minutes.

## 5. Results so far (per 100 games; nearly all games are won)

Current default (version 1.3), 5+0.05, vs Stockfish Elo 1500, 2,500 games:
9.1 full (of which ~0.9 classic), 49.8 near, 41 plain mates, 0.1 draws.
At 3+2 vs Elo 1500 / 2000 / 2500 (~250 games each): full 12.4 / 10.8 /
7.3; full or near 71.6 / 65.8 / 60.9.
Vs Maia-3 1100-2300 at 5+0.05: 8-13 full, 47-58 full or near.
Lichess (real bot account, mostly against strong bots): 136 games, +74
=62 -0; few smothers because strong bots rarely get decided early.

## 6. What we measured about WHERE smothers come from (today)

From 2,500 recorded games (1.3 defaults vs Elo 1500, 5+0.05). "Decisive"
= first moment our material lead >= 5 pawns (simple 1/3/3/5/9 count).

(a) Supply, not detection. With a large strict oracle (12 moves, 2 quiet,
    20M nodes, every defence must be smothered) on 600 won games: a
    strictly forced full smother existed at some point in only 9.2% of won
    games, and the engine delivered 53 of those 55. With the non-strict
    rule, 26% looked "available", but most of those were proofs the
    defender escapes by running into a quicker plain mate (which brutal
    mode declines), then the cycle repeats.

(b) Timing, our moves after the decisive point (median): full 26 (classic
    14), near 46, plain 80 (51% of plain wins stop exactly at the 80-move
    construction cap; only 19% of plain-mate games ever had any proof).

(c) Hazard: chance a game ends in a FULL smother during each block of 10
    of our moves after the decisive point:
      moves:    0-10  10-20  20-30  30-40  40-50  50-60  60+
      default:  0.7   2.3    2.7    2.8    0.6    0.2    ~0
      Full goal, 160 build moves:
                0.4   2.8    3.0    2.2    1.5    1.3    1.0-3.1 (to move 150)
    So construction produces full smothers at a roughly constant rate of
    ~0.25% per move; in the default it stops at move 40 because near
    smothers (which take 28% of games in moves 40-50) crowd them out.

(d) Which positions precede a full smother within our next 10 moves (base
    rate 2.2%, 92,509 positions in the first 40 moves after decisive):
    enemy king in corner 5.5%, edge 1.3%, centre 0.8%;
    ring squares not held by enemy pieces: 0 -> 29%, 1 -> 16%, 2 -> 3.2%,
    3 -> 0.9%, 4 -> 1.0%, 5+ -> 0.6%;
    we have a queen 2.7%, no queen 0.6%;
    number of our knights: 0 -> 2.8%, 1 -> 1.9%, 2 -> 1.5% (knights do NOT
    help AnyPiece smothers);
    enemy material (1/3/3/5/9): 0-4 -> 0%, 5-9 -> 2.0%, 10-14 -> 3.5%,
    15-19 -> 3.0%, 20-24 -> 2.2%, 25-29 -> 0.8%, 30+ -> 0.2%.
    Only 5% of positions have <= 1 open ring square.

(e) Enemy material at the decisive point does not differ between endings
    (median 26 for full, near and plain). Per game after the decisive
    point we capture 5.2 (full) / 6.6 (near) / 8.0 (plain) enemy units,
    about 40% of them recaptures; the defender captures 4.1 / 5.7 / 6.0.

(f) When a nearly closed box (<= 1 open ring square, king on edge or
    corner) dissolves, the cause (by our classification): a defender piece
    moves off the ring (most common), a defender pawn moves, the king moves,
    our knight is lost, and rarely our capture of a box piece.

(g) Promotions in winning games are almost all to a queen (some knights,
    rooks, bishops).

## 7. Everything already tried (do not re-propose without a new reason)

Gains that are in the defaults:
- Construction mode itself (full smothers from ~1-2 to ~8-12 per 100).
- Keeping enemy pieces alive (Keep weight), Hybrid near smothers after 40.
- Build-score weights tuned on game results (random search, 17 sets x 900
  games, then top sets, showdown of 4,000 games): full unchanged within
  noise (8.1 vs 7.75 per 100), full-or-near +4.5 at Elo 1500 (z ~4).

No gain or worse (each with 1,000-4,000 games per arm):
- More prover time; escape budget (extra prover time after the defender
  leaves a proof); starve guard; clock tweaks.
- Steering among MultiPV moves by "smother traps set" at all times
  (lost strength); starting construction earlier (more draws).
- Construction floor 400 / 250 instead of 600 (no gain, more draws).
- Blocker survivability terms (pinned / defended blockers, knight-can-win,
  pawn-push): defended 11.9 vs 10.7 (p ~0.14), others no better.
- Robust proofs (compare several proven first moves): 13.0 vs 12.1 (n.s.);
  strict proofs 12.2 (n.s.).
- Search control in construction mode: less LMR for our quiet moves that
  bring the knight closer / cover a ring square (+2.0 at 1500 in one run,
  -0.4 in a 3,500-game rerun; one time loss), less LMR for defender moves
  leaving the ring, no null move when the box is tight: none helped.
- Build-score terms: own queen/knight kept (OwnKeep), more weight on enemy
  pieces near their king (KeepNear 10, hurt), escape squares (Escape 6:
  +1.0, kept at 4), knight safety (hurt at 2500).
- SmotherFullExtra 3 / 6 / 12 and SmotherFullFirst 0 / 30 / 60 (prefer
  full over near more strongly in the prover): no gain.

## 8. Newest experiment (grid41, today, 5+0.05; per 100 games)

Elo 1500, 1,000 games per arm:
  arm                                  full  classic  near  full+near draws
  default (Hybrid @40, 80 build)        8.7   0.5    50.8   59.5      1
  Hybrid @80, 160 build moves          13.3   1.2    42.2   55.5      1
  Hybrid @120, 200 build moves         19.4   1.4    25.3   44.7     25
  Full goal, 80 build moves            15.1   1.3     2.2   17.3      1
  Full goal, 160 build moves           19.9   1.3     2.0   21.9      4
  Classic only, Full, 160 build moves   1.7   1.6     6.5    8.2      3
Elo 2500, 400 games per arm:
  default 4.2 full / 36.5 near; Hybrid @80/160: 8.2 / 31.5;
  Full 160: 14.8 / 0.8; Hybrid @120/200: 12.2 / 15.2 (9 draws, 1 loss on
  time); Classic Full 160: 1.5 / 4.5 (classic 1.2).
Median game length: default 137 plies; Hybrid @80/160 195; Full 160 227.

Running now (grid42): "SmotherNearHold": after the 40-move switch, keep
holding out for a full smother (up to N more build moves) while the ring
has <= 1 open square, or <= 2 with the king in a corner; elsewhere accept
near at once. Arms: hold 80 and 120 with 160 build moves; switch at 80
with hold 80; vs Elo 1500, 2500 and Maia-3 1500.

## 9. Constraints
- No measurable strength loss (construction only acts in decided
  positions, so strength risk is mainly draws or time losses in won
  games; still verified by SPRT before any default changes).
- Must work at bullet/blitz (5+0.05 to 3+2) and on Android phones;
  single binary; single thread is the test setting.
- Real use includes Lichess against humans, who often RESIGN lost
  positions long before mate; the longer we build, the more games end by
  resignation with no mate at all. Engine opponents in our tests never
  resign.
- Draws in won positions are a real cost (50-move rule, repetition).

## 10. What I want from you

1. The main question: the per-move rate of full smothers during
   construction is ~0.25% and has resisted every evaluation and search
   tweak we tried (section 7). What would RAISE THAT RATE, as opposed to
   just building longer? Give up to 6 concrete ideas, ranked by expected
   gain x chance of working, each with: the mechanism, exactly where in a
   Stockfish-style engine it goes (root decision, static eval at all
   nodes, prover, move ordering, time management), the cost, the risk,
   and a test design with our setup (arms, opponents, games).
2. The trade-off: building longer converts near smothers into full ones
   almost 1:1 (section 8). Is there a better rule than a fixed move count
   or our "NearHold" box rule for when to accept a near smother? Be
   specific about the decision rule and which measured features it uses.
3. Classic (knight) smothers: are about 1 per 100 and even a classic-only
   goal barely raises them (1.6). What would it take to raise them a lot,
   and is it realistic against limited Stockfish / human-like opponents?
4. With humans resigning, what is the best strategy for a Lichess bot that
   wants smothers (e.g. building faster, different goal, different
   thresholds)? Any trick that keeps a human from resigning is out of
   scope if it is unsportsmanlike.
5. Anything in our measurement or method that you think is wrong or
   misleading, and how to check it.
6. One long-shot idea that could double the full-smother rate.

Answer format: numbered ideas; for each, a one-line summary, then the
details. State every assumption you make that is not in this brief.
