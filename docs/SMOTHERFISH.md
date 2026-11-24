# Smotherfish guide

Smotherfish 1.5.1 is Stockfish (development version of 22 November 2026,
upstream commit 3e8fde75) with one extra goal: end the game with a
smothered mate. This guide explains how it works, lists every option, and
summarises what was measured. The day-by-day development log is in
`notes/HANDOFF.md`.

## The idea in one paragraph

A smothered mate needs the enemy king's own pieces on every square around it,
so it cannot be forced from most positions. Smotherfish therefore does three
things. It proves forced smothered mates when they exist and plays them, even
over a quicker ordinary mate. In brutal mode it treats every ordinary mate as
worth less than a smothered one. And once a game is decided, brutal mode
spends moves building the position a smother needs, instead of mating at
once. Against an opponent who plays well, the game is never decided, so the
engine plays ordinary Stockfish.

## How it works

### The smother prover (`src/smother.cpp`)

An AND/OR proof search:

- The attacking side may play checks, plus a limited number of quiet moves
  (`SmotherQuietMoves`) that threaten a smother.
- A proof must work against every defence. The defence that resists longest
  must end in a smothered mate; every other defence must lose to a strictly
  faster ordinary mate. So a defender who avoids the smother is mated sooner.
- Iterative deepening up to `SmotherMaxMoves` attacker moves, with its own
  proof table, node and time limits.
- A line that brings back a position already seen in the game or on the line
  is not a proof (otherwise a defender who escapes once escapes again, and the
  game can end in a draw by repetition).
- By default it runs in a thread next to the normal search
  (`SmotherParallel`) and, when it proves a smother, its line replaces the
  search's move.

Regression test: all 24,506 Lichess puzzles with the `smotheredMate` theme
(`notes/scripts/puzzles.py`). The prover proves 24,482 of them, every proof
is checked move by move, and none is wrong. The other 24 are smothers only in
the puzzle's main line, not forced under the rule above.

### Modes

- **Brutal mode off.** The prover runs with a small share of the move's time
  (`SmotherTimePercent`), more once the engine is clearly winning
  (`SmotherWinCp`, `SmotherWinTimePercent`). Otherwise the move is Stockfish's.
- **Brutal mode** (`SmotherBrutal`). In the search, an ordinary mate of the
  opponent counts as a sure win but below any smothered mate, so the engine
  prefers any smother it can see. When the engine is crushing
  (`SmotherBigCp`, or a forced mate), the prover searches deeper (12 moves,
  2 quiet) with more time (`SmotherBrutalTimePercent`). With a forced mate in
  hand it may use `SmotherMatePercent` of the remaining clock for at most 12
  moves per game.
- **Construction mode** (`SmotherBuild`, on by default, only with brutal
  mode). Once the game is decided (`SmotherBuildCp`, or a forced mate), the
  evaluation changes for at most `SmotherBuildMoves` moves per game:
  - At or above `SmotherBuildFloor`, extra advantage counts only one eighth.
    Below the floor the normal evaluation applies, so the engine never gives
    back more than that.
  - The construction score rewards the enemy king in a corner or on an edge,
    boxed in by its own pieces; the enemy pieces kept on the board (a smother
    needs blockers, and capturing them was the main way chances were lost);
    and our queen and knights close to it. In the measured
    games 77% of smothered mates were delivered against a king in a corner.
  - An ordinary mate counts no more than the floor, a smothered mate stays a
    real mate.
  - It switches off before the 50-move rule and when the budget is used up;
    the engine then mates normally.
- **Pondering.** While thinking on the opponent's time the prover searches
  deep and without limits (`SmotherPonderDeep`).

## Options

All options are standard UCI options. Defaults are what was measured best.

### Main switches

| Option | Default | Meaning |
| ------ | ------- | ------- |
| `SmotherMate` | true | Run the smother prover at all. |
| `SmotherBrutal` | true | Brutal mode (see above). The main switch for smother hunting; on by default since November 2026 (full-strength SPRTs: no cost). |
| `SmotherBuild` | true | Construction mode; only active with `SmotherBrutal`. |
| `SmotherGoal` | Hybrid | What counts as a smother in brutal mode: **Hybrid** (default: true smothers first, "all but one" ones after 80 construction moves), **Full** (only true smothers), **Near** ("all but one" ones always). See "Full, hybrid or near" below. |
| `SmotherClassic` | false | Count only knight smothers. By default any piece may deliver the mate. |
| `SmotherStrict` | false | Require a smother against every defence (no faster-mate escapes). Finds far fewer proofs. |

### Prover

| Option | Default | Meaning |
| ------ | ------- | ------- |
| `SmotherMaxMoves` | 8 | Longest proof, in attacker moves (12 when crushing in brutal mode). |
| `SmotherQuietMoves` | 1 | Quiet (non-checking) attacker moves allowed per line (2 when crushing). |
| `SmotherTimePercent` | 25 | Prover time, percent of the move's planned time. |
| `SmotherNodes` | 5000000 | Node limit per proof (lifted with a forced mate in hand in brutal mode). |
| `SmotherParallel` | true | Prove in a separate thread next to the search. |
| `SmotherPonderDeep` | true | Unlimited proving while pondering. |
| `SmotherRobust` | false | Compare alternative proofs and pick the hardest to escape. Measured worse; keep off. |

### Winning and brutal mode

| Option | Default | Meaning |
| ------ | ------- | ------- |
| `SmotherWinCp` | 300 | Advantage (centipawns) from which the prover gets more time. |
| `SmotherWinTimePercent` | 100 | Prover time when winning, percent of the planned time. |
| `SmotherBigCp` | 1000 | Brutal mode: advantage from which the deep prover runs. |
| `SmotherBrutalTimePercent` | 300 | Deep prover time, percent of the planned time (capped at 60% of the maximum). |
| `SmotherMatePercent` | 15 | Brutal mode with a forced mate in hand: share of the remaining clock per move. |
| `SmotherSeek` | 0 | Brutal mode off: moves per game in which ordinary mates count below smothers (brutal mode uses 200). |
| `SmotherSeekRule50` | 60 | No seeking or construction once the 50-move counter reaches this (half-moves). |

### Construction mode

| Option | Default | Meaning |
| ------ | ------- | ------- |
| `SmotherBuildCp` | 800 | Advantage (centipawns) at which construction starts. |
| `SmotherBuildFloor` | 600 | Advantage it never gives up while building. |
| `SmotherBuildMoves` | 160 | Most moves per game spent building (80 before 1.5). |
| `SmotherBuildWeight` | 8 | Centipawns per construction-score point. |
| `SmotherBuildWeights` | 13,8,23,8,2,4 | Construction-score weights: enemy pieces next to their king, open squares there, king in a corner, on an edge, our knights near it, our queen near it. Tuned on game results in 1.3 (was 12,10,25,10,4,3; see "Tuning" below). |
| `SmotherBuildKeep` | 11 | Construction-score points per enemy piece kept on the board (possible blockers). 3 until Nov 21, 8 in 1.2, 11 in 1.3. |
| `SmotherBuildKeepNear` | 2 | Extra points per enemy piece within two squares of its king. |
| `SmotherBuildEscape` | 4 | Points lost per square next to the enemy king that holds none of its pieces and that we do not attack (where a checked king steps out). |
| `SmotherBuildOwnKeep` | 0 | Experimental: points per queen and knight of ours kept. Measured: no gain. |
| `SmotherBuildKnightSafe` | 0 | Experimental: points lost per knight of ours near the king that is attacked and undefended. Measured: fewer smothers at Elo 2500. |
| `SmotherBuildLmr` / `SmotherBuildDefLmr` / `SmotherBuildNmp` | 0 | Experimental search control in construction mode (less reduction for box-building moves / for the defender's moves next to its king; no null move when the box is tight). Measured: no reliable gain. |
| `SmotherFullExtra` | 3 | After a near proof, how many moves longer a true smother may be and still be preferred. |
| `SmotherFullFirst` | 0 | Experimental: percent of the prover budget spent on a true smother before the near-smother search. Measured: no gain. |
| `SmotherBuildMaterialDiv` | 8 | Extra material above the floor counts 1/N. |
| `SmotherBuildStarve` | 0 | Experimental: points lost per unit of blocker reserve (enemy pieces minus open king squares) below `SmotherBuildStarveAt` (4). Measured: no gain. |
| `SmotherBuildTime` | 0 | Experimental: each construction move uses at least 1/N of the clock left. Measured: no gain. |
| `SmotherBuildSurvive` | 0 | Experimental blocker terms, a bit mask: 1 pinned blocker, 2 defended blocker, 4 blocker our knight wins, 8 pawn blocker that can step away. |
| `SmotherBuildSurviveCap` | 12 | Cap on those terms, in score points. |
| `SmotherBuildVersion` | 1 | 2 = construction-score weights fitted to game data (`notes/fit/`); better at predicting, not better in games. |
| `SmotherPartial` | false | "All but one" smothers always count (the same as `SmotherGoal` Near). |
| `SmotherPartialAfter` | 0 | "All but one" smothers count after this many construction moves (0 = never; `SmotherGoal` Hybrid uses 80, 40 before 1.5). |
| `SmotherHumanAfter` | 40 | Hybrid against a human opponent (`UCI_Opponent`): near smothers count after this many construction moves (0 = same as against computers). |
| `UCI_Opponent` | (empty) | Standard UCI opponent info from the GUI; only "human" / "computer" is used. |

### Other

| Option | Default | Meaning |
| ------ | ------- | ------- |
| `Analysis Elo` | 0 | For "go infinite" analysis (DroidFish's analysis mode): above 0, limits analysis depth to what the `UCI_Elo` limiter uses at that rating. 0 = full strength. |

### Older experiments (off by default)

`SmotherSteer`, `SmotherSteerFloor`, `SmotherSteerLines`, `SmotherSteerTime`,
`SmotherSteerWonOnly`, `SmotherTrapDepth`, `SmotherWinMargin`,
`SmotherWinLines`, `SmotherWinTrapDepth`, `SmotherWinTrapNodes`,
`SmotherWinSteerTime`, `SmotherMateDelays`, `SmotherMateSlack`: steering the
choice between near-equal moves towards smother traps. It did not raise the
smother rate and cost strength against strong opponents.
`SmotherShape`, `SmotherShapeCap`, `SmotherShapeAlways`: a small evaluation
bonus for smother-friendly positions; no measurable effect. Construction mode
replaced both.

## Full, hybrid or near

A true (full) smother needs every square next to the mated king filled by
its own pieces. An "all but one" smother leaves one square empty, but covered
by the attacker. Counting those as well changes how often a game ends with
the king buried in its own pieces, and what share of those are true ones.
Smothers per 100 games, brutal mode, 5+0.05:

| `SmotherGoal` | Elo 1500: true | Elo 1500: true + near | Elo 2000: true + near | Elo 2500: true + near |
| ------------- | -------------- | --------------------- | --------------------- | --------------------- |
| Full | 14.6 | 16.4 | about 8-9 | about 5-7 |
| Hybrid (default) | 8.4 | 53.1 (60.8 with pondering) | 43.8 | 38.3 |
| Near | 3.8 | 65.6 | 54.3 (true 2.5) | 45.7 |

(With `SmotherBuildKeep` 8, grid22 and grid23; Elo 2000 and 2500 for Full are
from earlier runs with keep 3. With keep 3 the Hybrid total at Elo 1500 was
35-38 and the Near total 56.)

When near smothers count, a true smother up to three moves longer is
preferred; that raised true smothers in Near mode from 1.6 to 3.3 per 100
games at Elo 1500 (0.4 to 2.1 at Elo 2000) with the same total. Near gives
the most smothers of either kind; Full gives the most true ones; Hybrid is
in between. Losses are rare (1 in 7,500 games of grid23, an ordinary blitz loss
at Elo 2000). Strength at full strength (SPRT, 6400
games at 10+0.1): Hybrid against brutal mode without it scored 0.502
(+1.4 Elo, 95% -0.5 to +3.3), so no strength cost.

## Measurements

All games: 5 seconds plus 0.05 seconds per move unless stated, balanced
8-ply openings (`notes/openings.txt`), paired colours, run on GitHub Actions
with `notes/scripts/match.py`. Opponents: Stockfish 19 with
`UCI_LimitStrength` and `UCI_Elo`, and Maia (human-like networks on lc0,
one node per move). Raw games are on the `actions-exp/<name>` branches under
`notes/results/`.

Smothered mates per 100 games:

| Setting | Elo 1500 | Elo 2000 | Elo 2500 | Elo 3000 | Maia 1100 | Maia 1900 |
| ------- | -------- | -------- | -------- | -------- | --------- | --------- |
| Brutal mode off | 1.1 | - | - | 0.2 | - | - |
| Brutal, no construction | 1.2-1.5 | 1.1 | - | 0.5 | 1.4 | 1.3 |
| Brutal, construction (20 moves) | 5.0 | - | - | 1.0 | 4.5 | - |
| Brutal, construction (40 moves) | 6.2-8.7 | - | - | - | - | - |
| **Brutal, construction (80 moves, default)** | **10.6-12.7** | **7.8** | **4.2** | **1.3-2.0** | **7.3-8.0** | **4.7** |
| Brutal, construction (200 moves) | 11.8 | - | - | - | - | - |

Strength: no losses in any of these runs. At Elo 3000 (600 games) the score
was 0.993 with brutal mode, 0.993 default, 0.994 with the smother features
switched off; with construction 0.995-0.997 (300 games).

Version 1.1 (newer Stockfish base, 98 upstream commits after Stockfish 19)
against version 1, both at full strength: 0.517 in normal mode (4000
games) and 0.517 in brutal mode (2000 games), about +12 Elo. Its smother
rate is unchanged (10.1 per 100 at Elo 1500; 1.5 at Elo 3000, score 0.994).
The measurements above were made with version 1; the opponent in them is
always Stockfish 19.

What did not help (kept as options, off): steering towards traps, a small
shaping bonus, picking the hardest-to-escape proof (`SmotherRobust`),
preferring strict proofs (none existed where it mattered), and a stronger
construction weight (16 halved the rate).

Starting construction earlier against strong opponents does not help: at
Elo 3000, a trigger of 4 or 6 pawns instead of 8 gave fewer smothers and more
draws (score 0.955 at 4 pawns). 15+0.15 games give the same rate as 5+0.05.

Pondering: with the engine pondering and the opponent thinking at least 1 s
per move, deep proving while pondering (`SmotherPonderDeep`) gave 12.2 vs
10.8 true smothers per 100 games at Elo 1500 and 9.0 vs 6.8 against Maia
1100. It also exposed a bug, now fixed: after "ponderhit" the engine could
wait up to about a second for a found proof's line to be rebuilt, which lost
three games on time.

Full-strength strength test (SPRT, 6400 games at 10+0.1, the method Fishtest
uses): every hunting feature on against the default engine scored 0.503
(+2 Elo, 95% 0 to +4). Hunting for smothers costs no strength against an
equal opponent.

Why ordinary play finds so few smothers: a forced smother exists in only 2-3%
of games, and opponents escape about half of them by walking into a faster
ordinary mate. Construction mode raises the number of positions where a
smother can be forced at all.

## Testing your own changes

- `./stockfish bench` must still report 1210779 nodes (the bench of the
  upstream base commit). The bench runs with brutal mode off; it switches
  it back on afterwards.
- `notes/scripts/puzzles.py ENGINE smothered.csv N SEED` re-runs the prover
  regression test (the CSV is the Lichess puzzle database filtered on the
  `smotheredMate` theme).
- Experiments: write `notes/exp/plan.json` and push it to a branch
  `actions-exp/<name>`; the workflow plays the games and commits the results
  and a summary table back to that branch. See `notes/HANDOFF.md`.
- Strength tests (SPRT): push `notes/exp/sprt.json` to an `actions-exp/<name>`
  branch; `sprt.yml` runs waves of games until the result is clear.
- CircleCI (free plan, a monthly credit pool): `.circleci/config.yml` runs
  the same plan files on 30 machines at once, on branches named
  `circle-exp/<name>`, for quick one-off tests. Its pipeline must be a native
  CircleCI pipeline, not one created from a GitHub Actions workflow.

## Version 1.5: build longer, score the box in steps

A diagnostic of 2,500 recorded games (notes/HANDOFF.md, Nov 23-24) showed
that while the engine builds, true smothers arrive at a steady rate (about
2.5% of games per 10 moves) until Hybrid starts accepting near smothers,
which then crowd them out; half of the plain-mate wins stopped at the
80-move construction cap. Holding out for a true smother longer converts
near smothers into true ones. Outside reviews (GLM, DeepSeek, ChatGPT)
suggested further terms; only a step-shaped ring score helped, by keeping
more near smothers as the fallback.

| Option | Default | Effect |
| ------ | ------- | ------ |
| `SmotherPartialAfter` (via Hybrid) | 80 | Near smothers count after 80 construction moves (was 40). |
| `SmotherBuildMoves` | 160 | Construction budget per game (was 80). |
| `SmotherBuildRingTable` | 60,50,0,-10,-15 | Build-score points by open squares next to the enemy king (0, 1, 2, 3, 4+), replacing the linear boxed/hole terms. Empty = linear. |
| `SmotherBuildReady`, `SmotherBuildDefRing`, `SmotherBuildExit` | off | Tested, no gain (ready squares trade near for true smothers; a lazier defender and a safe-exit penalty did nothing). |

5+0.05, smothers per 100 games (true / true or near): Elo 1500 (2,500 games
each): 1.4 defaults 8.2 / 59.6; 1.5 15.0 / 61.7. Elo 2500: 3.5-4.2 / 40;
1.5 about 9 / 43. 3+2 results are in the README. Against humans who resign
lost positions, longer building means some games end by resignation before
the mate; set `SmotherPartialAfter 40` and `SmotherBuildMoves 80` for the
old, quicker behaviour.

## Version 1.5.1: humans resign

Real players resign lost games: on Lichess (33 million human games,
Nov 2025 - Oct 2026, notes/scripts/lichess_db.py), a blitz player 9-14
points down resigns on about 6% of their moves, and only 23% of blitz games
where one side was 8+ points down end in mate. Against an opponent that
resigns on that measured curve (Maia-3 1500, 1,308 games per row; true /
near smothers per 100 games), 1.5 got 5.4 / 3.1; accepting near smothers
after 40 construction moves got 5.4 / 12.1: the same true smothers and
twice as many in total. So when the GUI says the opponent is human
(`UCI_Opponent` "title rating human name", sent by lichess-bot), Hybrid
switches after `SmotherHumanAfter` (40) moves; against computers and when
no opponent is given it stays at 80. Set `SmotherHumanAfter` 0 to turn this
off. Strength is unaffected (construction only acts in decided games).

## Tuning (version 1.3)

The construction-score weights were tuned on game results rather than on
predictions (a logistic fit to predictions, `SmotherBuildVersion` 2, was
better offline but worse in games). Batches of weight sets played 5+0.05
games against Stockfish at Elo 1500 and 2500, split over several GitHub
accounts; the best sets were re-tested with more games (notes/exp/tune*).

The winner (now the default) against the old defaults:

| Test | Old defaults | 1.3 defaults |
| ---- | ------------ | ------------ |
| 5+0.05, Elo 1500, 4000 games: full / full or near per 100 | 7.8 / 53.6 | 8.1 / 58.1 |
| 5+0.05, Elo 2500, 1500 games | 3.9 / 37.2 | 4.9 / 43.6 |
| 3+2, Elo 1500, 250 games | 12.9 / 59.8 | 12.4 / 71.6 |
| 3+2, Elo 2000, 250 games | 12.0 / 62.0 | 10.8 / 65.8 |
| 3+2, Elo 2500, 250 games | 8.0 / 49.2 | 7.3 / 60.9 |
| Strength, 10+0.1, 21,600 games (SPRT) | - | +1.3 Elo (95% +0.2 to +2.4) |

True smothers alone are unchanged; games ending in a full or near smother
rise by 4-12 per 100. No losses in these tests beyond 1 per 5500 games.

Measured and not adopted (notes/HANDOFF.md, grids 36-40): search-control
changes in construction mode, a true-smother-first prover, longer limits for
preferring a true smother, keeping our own mating pieces, knight safety and
holding back captures near the king. An analysis of 1000 won games
(notes/scripts/recall.py) showed why: the engine already delivers 53 of every
55 smothers that are forced against every defence; most of the rest are
proofs the defender escapes into a quicker ordinary mate.

## Human mode (HumanElo)

`HumanElo` N (default 0 = off, 1020 to 2400) makes the engine play like a
human of rating N. It sets the strength limit itself: below about 1860 the
lowest `UCI_Elo` limiter plus real mistakes (a share of moves picked at
random from the 8 best candidates; the limiter alone never loses more than
about a pawn per move), above it the `UCI_Elo` limiter alone. No other
option is needed; `UCI_LimitStrength`, `UCI_Elo` and `Skill Level` are
ignored while it is on.

Ratings are on the scale of the human-like Maia-3 network: N is the Maia-3
level the engine scores 50% against. Maia-3's levels are compressed (a
setting that scores 72% against level 1300 still scores 48% against 1900),
so the levels in between are fitted, about +-50 (+-100 near the ends). Measured at 5+0.05, 300
games per row:

| HumanElo | Limiter | Blunders | Measured (300 games each) |
| -------- | ------- | -------- | ------ |
| 1020 | 1320 | 13% | 47.3% vs 1100, 33.5% vs 1500 |
| 1255 | 1320 | 11% | 56.3% vs 1100, 40.0% vs 1500 |
| 1400 | 1320 | 9% | 62.0% vs 1100, 46.0% vs 1500 |
| 1490 | 1320 | 7.2% | 60.9% vs 1100, 49.6% vs 1500 (600 each) |
| 1580 | 1320 | 4% | 69.5% vs 1100, 62.5% vs 1300 |
| 1600 | (interpolated) | | 63.2% vs 1300, 45.3% vs 1700 |
| 1735 | 1320 | 1% | 68.8% vs 1300, 59.8% vs 1500 |
| 1800 | (interpolated) | | 63.3% vs 1500, 45.8% vs 1900 |
| 1880 | 1320 | 0 | 68.2% vs 1500, 47.8% vs 1900 |
| 2200 | (interpolated) | | 59.5% vs 1900, 42.0% vs 2300 (plays ~2115) |
| 2420 | 1455 | 0 | 76.8% vs 1700, 66.3% vs 2100 |

Values in between are interpolated. For a club player of about 1350, use
`HumanElo 1350`.

The underlying options stay available: `HumanBlunder` N (percent) or
`HumanBlunderPermille` N (per mille) add the mistakes to whatever
`UCI_Elo` / `Skill Level` is set. Ratings measured for them before
November 23 were too low (any blunder rate also widened the ordinary choice
from 4 to 8 candidates; fixed): `HumanBlunder 1` plays at about 1735, not
1350.

Proven smothered mates are still played in full.
