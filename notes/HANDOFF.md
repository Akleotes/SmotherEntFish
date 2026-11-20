# Handoff note for the next session

Written because the user is continuing this work in another session. Nothing
here is finished: read "State" first, then "Next steps".

## What the user asked for (original request)

1. Set up Stockfish 19 (official repo, tag `sf_19`), apply `smother-mate-v2.patch`
   with `git am`, build, confirm bench 2497913 and the puzzle harness gives
   2348/2350 with 0 bad.
2. Work on the README's "Next goal": smarter, stronger steering for more
   smothered mates, keeping a win rate above 50% against Stockfish with
   UCI_Elo 3000 (revised from 2500: the user measured Stockfish 19 at about
   3804 Elo, so 3000 is the new bar; it is inside the UCI_Elo range
   1320-3190). Use all CPU cores for matches.
3. When done, build static Android binaries with the NDK for DroidFish.
4. Added later by the user: the engine should be able to smother the opponent
   with high likelihood at any Elo, not only at the level where smothers
   happen by themselves. Measure the smother rate (smothered mates per game
   won, and per game overall) at several UCI_Elo settings, for example
   1500, 2000, 2500 and 3000, and aim to raise it at each one. Set a numeric
   target only after the first measurements exist, because nothing has been
   measured past the 1500 baseline yet. This goal does not replace the
   win-rate constraint against 3000 in item 2.

The user's handoff zip (`smother-stockfish-handoff.zip`, with README.md,
patch, tests/, match/) is not in the repo. Ask the user to re-upload it if
the new session does not have it. The patch itself is already applied here.

## State

Branch `ccr-22798bd9-4zky9t` (PR #1) holds: sf_19 + the 4 patch commits + my
steering commit + a clang-format 20 commit. It is based on the `sf_19` tag, not
on this repo's `master` (a newer Stockfish), so the PR diff against `master`
also shows the version differences.

Done and verified:
- bench is 2497913 with the patch and with my steering code (default off).
  Unpatched sf_19 also gives 2497913.
- Puzzle harness: positions=2350 claimed=2348 verified=2348 bad=0. That is
  the full run on the patched build before my steering changes (steering is
  off by default and does not touch the prover, but re-run it once after any
  prover change). It takes about 15 minutes on one core.
- Matches vs Stockfish 19 at UCI_Elo 1500, tc 5+0.05, 1 thread, Hash 16,
  4 concurrent games, 8moves_v3 book:
  - SmotherSteer=0: 200 games, 200 wins, 0 smothered mates.
  - SmotherSteer=150: stopped early at 94 games, 94 wins, 0 smothered mates.
    I could not tell whether steering fired at all: fastchess's log does not
    contain `info string` lines, so the "smother steer" message was never
    visible. Verify this first (see Next steps, item 1).

Not done:
- No measurement of smothers per 100 games at Elo 1500 or 2000 with steering.
- No win rate vs UCI_Elo 3000 at all (the key constraint, must stay above 50%).
- No tuning of the new options.
- The Android build has not been run. The NDK is not in the repo; see below.

## What I changed (commit "Smother steering: prove traps per opponent reply")

`src/smother.{h,cpp}`: `Smother::traps()`. For a position with the opponent to
move, it tries every legal reply and runs the prover (depth `SmotherTrapDepth`,
4096 nodes, reusing the shared proof table via `Limits::keepTable`). It returns
the plausibility-weighted share of replies that lead into a forced smother
(replies that lose material by SEE count 0.3, others 1.0).

`src/search.cpp` (`start_searching`): the steering block now scores each
MultiPV candidate within the margin by
`100*trapShare + 50*(expected reply is a trap) + 0.5*potential - 0.05*loss`
and switches only if the winner beats the best move's score by 5 or more.
Steering stays off unless `SmotherSteer > 0`. When already winning, it never
picks a move whose score is below `SmotherSteerFloor`; when not winning the
margin shrinks to a quarter. "Mate phase": if the best move already has a
forced plain mate, a slightly slower mate (within `SmotherMateSlack` score
units, i.e. plies) may be chosen for its traps, at most `SmotherMateDelays`
times per game (counter reset in `Worker::clear()`).

New UCI options (engine.cpp): SmotherSteer (0-500, default 0),
SmotherSteerFloor (150), SmotherSteerLines (4), SmotherSteerTime (15, percent
of the move's time), SmotherTrapDepth (3), SmotherMateDelays (8),
SmotherMateSlack (6).

Known weak spots to check before trusting it:
- The mate-phase check `rm.score < VALUE_MATE_IN_MAX_PLY` and the slack are in
  raw score units (1 per ply); the `loss * 10` there is only a utility
  weight. Sanity test it on a position with a plain forced mate.
- Steering needs `SmotherSteerLines` MultiPV lines, which lowers search
  strength a little at a fixed time. The 3000 win rate must be measured.
- The trap scorer allows at most one quiet move (`min(1, SmotherQuietMoves)`).
- The model of the opponent is crude. UCI_Elo 1500 picks among shallow lines
  at random, so "plausible reply" weighting by SEE is a guess.

## Next steps (in order)

1. Make steering observable. Run one steered game by hand (or set fastchess
   engine logging so `info string` lines are kept) and count "smother steer"
   lines. If it never fires, debug before running more matches.
2. Measure smothered mates per 100 games vs UCI_Elo 1500 and 2000 for
   SmotherSteer 0, 100, 150. Use several hundred games per setting (the
   Elo 1500 baseline of 200 games gave 0 smothers, so expect low counts and
   plan sample sizes accordingly).
3. Measure the win rate vs UCI_Elo 3000 for the steering settings that look
   good. It must stay above 50%. Use all cores. Expect this to be much harder
   than 1500: at 3000 the opponent rarely blunders into smothers, so a win
   rate above 50% may require the steering to cost little strength.
4. Tune (`SmotherSteerFloor`, margin, `SmotherTrapDepth`, trap node budget).
5. Re-run bench (2497913) and the puzzle harness (2348/2350, 0 bad).
6. Android build with `notes/scripts/build_android.sh` (below). Copy outputs into
   DroidFish's `uci/`. Never name the binary `stockfish` or `*.ini`.
7. Update the PR description with the results.
8. For the any-Elo smother goal (request item 4): after step 2, produce a
   table of smother rate per UCI_Elo (1500, 2000, 2500, 3000) for each
   steering setting, with game counts. Use it to decide where the steering
   should be strongest, and check that the 3000 win rate from step 3 holds.

## Environment notes (the container is ephemeral; rebuild all of this)

- Network: the default environment blocks the net download. I created a personal
  environment "Smotherfish" allowing `tests.stockfishchess.org`,
  `data.stockfishchess.org`, `dl.google.com` and `raw.githubusercontent.com`.
  A new session needs the same hosts. `make net` in `src/` then works
  (the net is `nn-1a298aa575a0.nnue`).
- Build: `cd src && make -j build ARCH=x86-64-bmi2` (this machine had 4 cores,
  AVX2/AVX512).
- Python checker: the system pip cannot build `chess`. Use a venv:
  `python3 -m venv v && v/bin/pip install -U pip setuptools wheel chess`.
- Formatting: the repo's CI uses clang-format 20. `pip install "clang-format==20.*"`
  and run `clang-format -i` on changed files (Ubuntu's clang-format 18 cannot
  read the repo's `.clang-format`).
- Matches: `git clone https://github.com/Disservin/fastchess` and `make -j`;
  book: `books/8moves_v3.pgn.zip` from official-stockfish/books (a plain git
  clone works for it; LFS is not needed). Build a clean Stockfish 19 from the
  `sf_19` tag as the opponent (`git archive sf_19 src scripts`, then add the
  net). `notes/scripts/match.sh` runs one setting (edit the paths at the top).
- Android: NDK r27c from
  `https://dl.google.com/android/repository/android-ndk-r27c-linux.zip`
  (about 660 MB). `notes/scripts/build_android.sh` builds `armv8-dotprod` and `armv8`
  static binaries and strips them (edit the paths at the top).
  A glibc-static build does not start on Android; use the NDK build.
- Scripts in `notes/scripts/` have my scratchpad paths hard-coded. Edit them.

## Update from the follow-up session

Step 1 is done. Steering never fired because of two bugs, fixed in commit
"Fix smother steering never firing" on branch `ccr-00291b96-tkvbkh`:
- `Smother::traps` got `threads.stop`, which is already set after the search,
  so every reply was aborted with 0 nodes. It now gets its own flag.
- Timed searches stop inside the last MultiPV iteration, leaving lines 2..N at
  `-VALUE_INFINITE`; only the best move was a candidate. Those lines now use
  their exact `previousScore`.
After the fix, 3-4 candidates are scored per move and steering fires in games.
Bench is unchanged (2497913). In the few moves inspected, the trap share was
0% and the one steer seen was chosen on "potential" alone, so check the trap
scoring during step 2. The puzzle harness has not been re-run since the fix.
Cloning/building fastchess was blocked by the session's permission check;
steps 2-3 still need it.

### Match tooling without fastchess

Cloning outside GitHub repos (fastchess, books, official Stockfish) is refused
in these sessions (GitHub access is scoped to this repo). Instead:
- Opponent: `git archive edb0d9db src scripts` (stock Stockfish 19, in this
  repo), add the net, build. Bench 2497913.
- `pip install chess` in a venv (PyPI works).
- `notes/scripts/make_book.py ENGINE 300 openings.txt` makes balanced 8-ply
  openings (`notes/openings.txt` is the set used).
- `notes/scripts/match.py OUT.jsonl OURS OPP ELO GAMES --opt SmotherSteer=150`
  plays paired games, 5+0.05, 4 concurrent, real clocks, and records
  smothers and steer lines per game.
- `notes/scripts/summary.py res/*.jsonl` prints the table.

### First-pass grid (steering fix applied, 5+0.05, 200 games each, vs stock SF19 UCI_Elo N)

```
file                         games    W    D    L  score  +-95% smoth class  /100g  /100W steer/g time
e1500_s0.jsonl                 200  200    0    0  1.000  0.000     5     1    2.5    2.5    0.00    0
e1500_s150.jsonl               200  199    1    0  0.998  0.005     5     1    2.5    2.5    0.62    0
e2000_s0.jsonl                 200  199    1    0  0.998  0.005     1     0    0.5    0.5    0.00    0
e2000_s150.jsonl               200  196    4    0  0.990  0.010     0     0    0.0    0.0    0.69    0
e2500_s0.jsonl                 200  198    2    0  0.995  0.007     1     0    0.5    0.5    0.00    0
e2500_s150.jsonl               200  195    5    0  0.988  0.011     0     0    0.0    0.0    0.52    0
e3000_s0.jsonl                 200  187   13    0  0.968  0.017     0     0    0.0    0.0    0.00    0
e3000_s150.jsonl               200  163   36    1  0.905  0.028     0     0    0.0    0.0    0.64    0
```

"smoth" uses the engine's AnyPiece definition, "class" = knight mate.
Findings: steering as designed does not raise the smother rate at any Elo
(1500: 5 vs 5; 2000/2500: 1 vs 0), it fires ~0.6 times per game, and it costs
strength at 3000 (0.968 -> 0.905). The 50% bar vs 3000 is far from binding
(90-97%), so there is a lot of strength to spend on smothers.
Raw games are in notes/results/*.jsonl.

### Session 2 findings (won mode, shaping, seek, brutal)

Elo 1500, 400 games each, smothers per 100 games: won mode 1.0, shaping
0.2-1.0, won-mode steering 1.0, seek mode 1.0, SmotherBrutal 1.2. Scores
0.998-1.000. Elo 3000, 300 games: default 0.982, SmotherSeek=30 0.980.
Ceiling: in 200 won brutal games at 1500, a forced smother (12 moves,
3 quiet, non-strict) existed in only 10 games, 3 delivered. Every strictly
forced smother was delivered. End-game methods are capped near 5/100 games;
gains must come from earlier (openings, middlegame plans).
Raw games: notes/results/exp1, exp2 branches exp2-w1..w3.

### Session 2, overnight (Nov 20 JST)

Experiments now run on GitHub Actions (`.github/workflows/smother-exp.yml`):
push `notes/exp/plan.json` to a branch `actions-exp/<name>`; results are
committed back to that branch under `notes/results/<exp>/`. Plans can use
Maia opponents (`"opponent": "maia-1500"`, lc0 built in CI, `go nodes 1`).

Findings:
- grid1 (2000 games/setting): default, brutal, middlegame shaping and their
  combinations all give 0.6-0.9 smothers/100 games at Elo 1500/2000 and
  0.2-0.3 at 3000; scores unchanged (0.97-1.00).
- Traces of lost chances at Elo 1500: ~60% were never started because the
  prover ran out of time (needs 0.1-3M nodes); the rest the opponent escaped.
- grid2: more brutal prover time (300%/600%) did not help, because brutal
  mode spent the budget on every move and ran its own clock down (median
  lowest clock 0.45 s vs 1.73 s default, measured in match records).
- Every one of 41 traced smother chances arose at >= +15 pawns or with a
  mate on the board (only 28% of positions are >= +10). The deep prover in
  brutal mode is now gated on SmotherBigCp (1000) -> grid3b measures it.
- SmotherRobust (choose the hardest-to-escape proof) and larger/faster
  prover tables were tried and rejected (measured, no net gain).
- SmotherPonderDeep: while pondering the prover searches deep and
  unbounded; smothers needing 2-3M nodes are found after 3 s of pondering.
  This matters for real games against people (long thinking times); our
  matches cannot measure it (opponents move instantly or share the CPU).
- Maia runs hung in CI: Pool workers died when an engine failed at start-up
  and were respawned forever; fixed (lazy engine start, watchdog, hang
  records). A debug stack-dump timer armed before fork also deadlocked
  workers; fixed.
- Prover regression test (replaces the zip's puzzle harness): all 24,506
  Lichess `smotheredMate` puzzles (CC0), `notes/scripts/puzzles.py`.
  Current build and the build before tonight's prover changes both give
  claimed=24482 verified=24482 bad=0. The 24 unclaimed are smothers only in
  the puzzle's main line (another defence avoids them and is not mated
  faster), so not forced under the prover's rule.
- grid3b (deep prover only when crushing): no gain at 1500/2000/15+0.15
  (0.6-0.8 smothers/100) and no cost at 3000 (0.981 vs 0.973). In-game
  proof records: ~1.5% of games at 1500 reach a proven smother and only
  ~50% of those end in one, because the prover's rule lets the defender
  escape into a faster plain mate and weak opponents do.
- Maia grid (human-like, 1000 games each): smothers per 100 games, default
  vs brutal: Maia 1100 2.0 vs 1.4, Maia 1500 0.6 vs 0.8, Maia 1900 1.8 vs
  1.8. Scores 0.994-0.999. Same picture as against Stockfish at UCI_Elo.
- Bug fixed: in seek mode a plain forced mate is a TB-range score, which the
  won/crushing gates did not accept, so the prover lost its budget right in
  the mating phase (a smother in 7 needing 38k nodes was missed after an
  escape). grid4 measures the fix.
- Android: `.github/workflows/android-build.yml` (push to
  `android-build/<name>`) builds static armv8 / armv8-dotprod binaries with
  NDK 27.2, checks bench 2497913 under qemu, uploads artifacts.

### Session 2, morning (Nov 20 JST)

Three bugs, all fixed:
- Prover loop (commit 6a5db802). In 6 grid4 games a proven smother ended
  in a draw: the defender escaped into a quicker plain mate, the engine
  declined that mate for the same smother line, and the moves went round
  in a circle until threefold. The prover now fails any attacker move on a
  smother line that brings back a position seen before (in the game or on
  the line). Replays: 4 of the 6 now mate at once, 2 mate within 3-9 plies.
  Puzzle regression unchanged (24482/24482, 0 bad, 0 differences).
- Match runner draws (same commit). `can_claim_draw()` also counts a
  threefold the side to move *could* make next, so games ended as draws
  that the winner would never have repeated. All but 1 of ~250 draws in
  grids 1-4 were of that kind; the scores above are understated (mostly at
  Elo 3000). Now only a real third occurrence or fifty moves ends a game.
- Match runner hang (de9d6354). A Pool worker that dies loses its game and
  Pool waits forever (one grid4 job sat until the 90-minute timeout). With
  no finished game for `MATCH_STALL` seconds (600) the run now ends with
  the games so far.

grid5 (both fixes, 5+0.05; Maia runs are 1000 games, Elo 3000 runs 600):

```
file                     games    W    D  L  score  smothers /100g  proof games  delivered
e1500_brutal              2000 2000    0  0  1.000        25   1.2   61 (3.05%)  41%
e1500_default             2000 2000    0  0  1.000        22   1.1   43 (2.15%)  51%
e2000_brutal              2000 2000    0  0  1.000        22   1.1   37 (1.85%)  59%
maia1100_brutal           1000 1000    0  0  1.000        14   1.4   24 (2.40%)  58%
maia1900_brutal           1000 1000    0  0  1.000        13   1.3   24 (2.40%)  54%
e3000_brutal               600  591    9  0  0.993         3   0.5    3          3/3
e3000_default              600  591    9  0  0.993         1   0.2    1          1/1
e3000_off (SmotherMate=false) 600 593  7  0  0.994         1   0.2    -          -
```

- With real draw rules: 8,000 games at Elo 1500/2000 and vs Maia, all won.
  At Elo 3000 the smother features cost nothing measurable (0.993 vs 0.994
  with them off) and the win-rate goal (>50%) holds by a wide margin.
- Smother rate is still ~1.1-1.4 per 100 games; brutal vs default is
  within noise. Brutal still uses more clock (median lowest clock 0.66 s
  vs 1.36 s at 1500; 0.21 s at 3000), with 0 time losses in 9,200 games.
- Escapes: an escaped game ends 3-5 plies after the last proof (the
  defender steps into a mate in 1-2). No strict proof (every defence
  smothered) existed at the first chance in any of 57 escaped games, so
  preferring strict proofs cannot help. But in 17 of 55 after-escape
  positions (with the game history; 20 without) a new smother in 6-9 is
  still forced. It needs 0.3-11M prover nodes (~3M nodes/s), while by then
  the clock is 0.5-1.5 s at 5+0.05.
- Mate-in-hand budget (commit 25407786, brutal only): with a forced mate
  in hand the prover may use `SmotherMatePercent` (15) of the remaining
  clock, without the node cap, for at most 12 moves per game. 48 local
  games at 5+0.05: no time losses. grid6 measures it at 5+0.05 and as an
  A/B at 15+0.15.
- Android build of de9d6354 passed (run 44633063886, bench 2497913 under
  qemu); it does not include the mate-in-hand budget yet.

grid6 (mate-in-hand budget; same openings as grid5):

```
file                          games    W  D  L  score  smothers /100g  proof games  delivered
e1500_brutal_hand  (5+0.05)    2000 1999  1  0  1.000        22   1.1   57           39%
e1500_brutal_tc15_hand          1000 1000  0  0  1.000        14   1.4   43           33%
e1500_brutal_tc15_nohand        1000 1000  0  0  1.000        11   1.1   42           26%
e3000_brutal_hand              600  590  9  1  0.991         3   0.5    4           3/4
```

- 5+0.05: no gain (22 vs 25 in grid5): by the time a forced mate is in
  hand the clock is too low for 15% of it to buy a 1M+ node proof.
- 15+0.15 A/B: 14 vs 11 smothers, not significant, in the expected
  direction. Kept: no cost seen (no time losses, clocks unchanged), and
  real games are slower than these matches.
- The one Elo 3000 loss is an ordinary blitz loss: at ply 36 (3.2 s on the
  clock) the engine played Rxf6, -6.6 at depth 20; stock Stockfish 19 plays
  the same move 8/8 times at that clock. Elo 3000 scores, grid5/6: 0.991
  brutal+hand, 0.993 brutal, 0.993 default, 0.994 smother features off.

Where this leaves the smother rate: ~1.1-1.4 per 100 games against weak
and human-like opponents in 5-15 s games, with no strength cost. The
limits measured: a proven smother appears in ~2-3% of games; the defender
escapes ~50-60% of them into a quicker plain mate; strict proofs do not
exist in those positions; re-proofs after an escape need more time than
blitz gives. Most remaining levers are earlier in the game (openings,
middlegame plans that keep the enemy king boxed in), as noted before.
Ponder-time proving (SmotherPonderDeep) and the mate-in-hand budget only
show in slower games, which these matches do not cover.

Android, final code (commit 70d42651; later commits are notes only): run
44642135912 passed (bench 2497913 under qemu). Artifacts
`smotherfish-android-armv8-dotprod` (most phones since ~2019) and
`smotherfish-android-armv8`, kept until 2026-12-20:
https://github.com/Demonic1594/Smotherfish/actions/runs/44642135912
In DroidFish: copy the binary to the phone and pick it as an engine; do not
rename it to "stockfish". Brutal mode: set `SmotherBrutal` to true in the
engine options.

### Session 3 (Nov 20 JST, morning): construction mode

- grid7, `SmotherRobust` (greedy-weighted choice among alternative
  proofs) in brutal, same openings as grid5: 53 smothers from 117 proof
  games vs 74 from 146 without it. Rejected for good (it costs proofs).
- Escape study (306 proof games): opponents leave the smother line mostly
  at their first reply (74 of 134 escapes), usually with only 2-3 legal
  moves; in 29 escapes they grabbed a piece instead of the needed king move
  or block. Baiting with a sacrifice does not convert better (24-30%).
- Delivered smothers (227): 77% with the king in a corner, all on an edge,
  blocked mostly by its own pawns, rooks and bishops.
- Construction mode (commits 8a938b32, 4784aa00; `SmotherBuild`, off by
  default): once decided (`SmotherBuildCp` 800 or a forced mate), above
  `SmotherBuildFloor` (600) extra material counts 1/8 and
  `Smother::build_score()` (corner, own blockers, enemy pieces kept, our
  queen/knights close) counts `SmotherBuildWeight` (8) cp per point; a
  plain mate counts as the floor. `SmotherBuildMoves` per game (20).

grid8 (600 games each, 5+0.05 unless noted, Elo 1500 unless noted):

```
setting                     smothers /100g  proof games  score
brutal, no construction            9   1.5      16       1.000
build (20 moves)                  30   5.0      49       1.000
build, 40 moves                   52   8.7      85       0.999
build, 15+0.15                    33   5.5      62       1.000
build, weight 16                  15   2.5      30       1.000
build vs Maia 1100                27   4.5      42       1.000
build vs Elo 3000 (300 games)      3   1.0       3       0.997 (0 losses)
```

First method that moves the rate several-fold. grid9 measures budgets
40/80/200 and Elo 2000 / Maia 1900 / Elo 3000 at 80.
Idea queued (from an outside review): score blocker survivability in
build_score() (pinned/protected blockers vs ones that can capture our
knight or step away).

grid9 (construction budget; 600 games each, 300 at Elo 3000):

```
setting                 smothers /100g  non-wins                 score
Elo 1500, budget 40          37   6.2   0                        1.000
Elo 1500, budget 80          76  12.7   0                        1.000
Elo 1500, budget 200         71  11.8   3 draws, 5 at 400 plies  0.993
Elo 2000, budget 80          47   7.8   1 draw                   0.999
Maia 1100, budget 80         44   7.3   1 draw                   0.999
Maia 1900, budget 80         28   4.7   2 draws                  0.998
Elo 3000, budget 80           6   2.0   2 draws                  0.997
```

Commit 97256b6f: construction mode on by default in brutal mode, budget
80. Games are longer (median ~120 plies vs ~53). No losses in any run.
Android build of it: run 44654465325 (artifacts until 2026-12-20).
Commits 0b8bc9f5, 6f95b567: optional blocker survivability,
`SmotherBuildSurvive` bit mask (1 pinned +4, 2 defended +2, 4 our knight
wins it by SEE -4, 8 pawn blocker can step forward -3; capped +-12).
With 0 the search is identical to before (40/40 positions, same move and
nodes at depth 12). grid10 measures 0 / 3 / 15 and each bit alone.

grid10 (blocker survivability, budget 80; 1000 games each at Elo 1500):

```
SmotherBuildSurvive        smothers /100g (95%)   proof games  delivered  W/D/L
0  control (A)                  106  10.6 +-1.9   154          69%        997/3/0
1  pinned bonus                  99   9.9          166          60%        999/1/0
2  defended bonus               132  13.2 +-2.1   181          73%        999/1/0
3  pinned+defended (B)           89   8.9          146          61%        995/5/0
4  knight-SEE penalty           100  10.0          149          67%        997/3/0
8  pawn-push penalty            117  11.7          153          76%        999/1/0
15 all (C)                      108  10.8          158          68%        999/1/0
Maia 1100 (600): A 8.0, C 6.2.   Elo 3000 C (300): 1.3, 0.995, no losses.
```

Inconclusive: "defended" alone +2.6 (p ~0.07) but bad combined with
"pinned"; nothing else separates from the control. Default stays 0.
grid12 re-tests 0 / 2 / 10 with 2000 new games (Elo 1500) and 1000 vs
Maia 1100. grid11 tests the Elo 3000 trigger (800/600/400 vs off), Elo
2500 and 15+0.15. Also: `SmotherBuildSurviveCap` (default 12) for a cap
ablation if a survivability setting wins.
