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
