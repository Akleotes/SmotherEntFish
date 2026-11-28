# Changelog

All releases are on the [Releases page](https://github.com/Demonic1594/Smotherfish/releases).
Strength figures are Elo against the previous version at full strength
(SPRT, 10 seconds + 0.1 per move) unless stated; smother figures are per 100
games. The full record of every experiment is in `notes/HANDOFF.md`.

## 1.7 (28 November 2026): newer Stockfish

- **Stronger:** Stockfish's latest search and network (upstream commit
  `88337401`, network `nn-684d0e60e71d`) merged in: +1.7 Elo against 1.6 over
  76,000 games (95%: +1.1 to +2.3). Bench 1128273.
- **Smothers unchanged:** on the same openings, 3.12 knight smothers per 100
  games pooled against 3.19 for 1.6 (within the noise), no losses.
- **HumanElo refitted:** the new engine's `UCI_Elo` limiter plays weaker at the
  same setting, so the rating map was refitted and measured against 1.6 at
  1580, 1700, 1735, 1880, 2200 and 2400: each rating plays as it did in 1.6.
- New experimental options, off by default, each measured with no gain: a
  zugzwang-aware prover (`SmotherProverZugzwang`, `SmotherProverThreatQuiet`),
  knight keeping (`SmotherKnightKeep`, `SmotherKnightKeepCp`), a prover budget
  after an escape (`SmotherEscapeMoves`, `SmotherEscapePercent`), a stalemate
  check in construction (`SmotherBuildStalemate`) and once-repeated positions
  on smother lines (`SmotherRepeatOnce`).
- Volunteer network: Helper kick no longer stops at an unreachable fork.

## 1.6 (26 November 2026): knight smothers

- **Plays for the textbook smothered mate:** a knight mates a king that its own
  pieces box in on every side. Knight smothers against Stockfish `UCI_Elo` 1500
  rose from 0.7 to 3.8 per 100 games (5+0.05, 2,500 games), against Maia-3 1500
  from 0.3 to 3.3, and at 3+2 from 0.9 to 3.7 (Stockfish 1500) and 1.4 to 6.3
  (Maia-3).
- New defaults: `SmotherClassic true`, `SmotherBuildKnightCheck 16` (a knight on
  its way to a checking square), `SmotherCrushMoves 16` and `SmotherCrushQuiet 3`
  (a deeper prover once the game is decided). `SmotherClassic false` restores
  1.5.1's aim.
- Strength: -0.3 Elo against 1.5.1 over 32,400 games (95%: -1.2 to +0.5).
- New experimental options, off by default: a learned linear model
  (`SmotherBuildModelScale`) and a small neural network (`SmotherBuildNetScale`)
  as the construction score, and a decoy term (`SmotherBuildDecoy`). The UCI
  command `smothernet` prints the network's inputs and output.
- 29 experimental options that never beat the defaults were removed; the engine
  plays exactly as with their old defaults (verified move for move on 300
  positions). See the guide, "Removed options".
- Lichess bot: no games under one minute, at most two games per bot per hour.
- New: a volunteer test network (`docs/HELPING.md`) and a live
  [test status page](https://demonic1594.github.io/Smotherfish/).

## 1.5.1 (24 November 2026): human opponents resign

- When the GUI reports a human opponent (`UCI_Opponent`, sent by lichess-bot),
  near smothers are accepted after 40 construction moves instead of 80, because
  people resign lost games (measured on 33 million Lichess games). Against an
  opponent resigning on the measured curve, true smothers were unchanged (5.4 per
  100) and all smothers doubled (17.5 vs 8.5).
- New option `SmotherHumanAfter` (0 = off). No change against computers.

## 1.5 (24 November 2026): build longer for true smothers

- Construction holds out for a true smother for 80 moves (was 40) and may last
  160 moves (was 80); the king's box is scored in steps
  (`SmotherBuildRingTable`).
- True smothers at 5+0.05 roughly doubled against Stockfish 1500-2500 (8 to
  14-15 and 4 to 8-9 per 100). Strength: -1.0 Elo against 1.4.1 over 18,000
  games (95%: -2.2 to +0.1).

## 1.4.1 (24 November 2026): HumanElo recalibrated

- `HumanElo` measured directly against Maia-3 (300 games per point); range 1020
  to 2400. Full-strength play unchanged.

## 1.4 (23 November 2026): HumanElo

- `HumanElo` N plays like a human of rating N, setting the strength limit and
  the rate of real mistakes itself.
- Fixed: in 1.3 any `HumanBlunder` above 0 also weakened every ordinary move.

## 1.3 (November 2026): tuned construction

- Construction weights tuned on game results: games ending in a full or near
  smother at 3+2 rose to 71.6 per 100 against Stockfish 1500 (from 59.8), 65.8
  against 2000 (62.0) and 60.9 against 2500 (49.2).
- Strength: +1.3 Elo against 1.2 over 21,600 games (95%: +0.2 to +2.4).
  At 60+0.6 against unmodified Stockfish: +0.5 Elo over 7,320 games.
- `HumanBlunder`: real mistakes on top of the `UCI_Elo` limiter.

## 1.2 (November 2026): brutal mode by default

- Brutal mode and construction mode on by default; enemy pieces kept on the
  board while building (`SmotherBuildKeep`). Against unmodified Stockfish:
  -0.3 Elo over 43,200 games (95%: -1.1 to +0.4).

## 1.1 (November 2026): newer Stockfish base

- Rebased on the Stockfish development version after Stockfish 19 (98 upstream
  commits): +12 Elo against 1.0 over 4,000 games, same smother rate.

## 1.0 (November 2026): first release

- The smothered-mate prover, brutal mode and construction mode.
