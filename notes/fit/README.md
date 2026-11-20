# Fitting the construction score to game data

Offline, no new games: which `Smother::build_score()` terms predict that a
smother follows, and with what weights.

## Method

- `features.py OUT.npz FILES...` replays match records (notes/results and
  the `actions-exp/*` branches). At every position where we are to move, not
  in check, and ahead by at least 8 pawns of material (a stand-in for
  "decided": construction mode starts at +8, and the records have no
  evaluations), it records the build_score terms plus candidate terms.
  Labels: `y20` = the prover proved a smother within the next 20 plies;
  `ys` = the game ended in a smother we delivered.
- `fit.py DATA.npz [y20|ys]` fits a logistic regression (standardised
  terms, 5-fold cross-validation grouped by game) and prints the AUC of the
  hand-set weights, of each term alone, and of the fitted weights, scaled
  so that `boxed` = 12 as in build_score.
- `mates.py FILES...` counts, over our mates, how many squares next to the
  mated king were "open" (neither its own pieces nor the checker's square):
  0 = smother, 1 = "all but one" (SmotherPartial), and where the king stood.

Two data sets (Nov 2026):
- A: games without construction mode (grids 4-7, grid8 base; brutal and
  default, Elo 1500/2000, Maia). 26,599 games, 149,855 decided positions,
  2.3% followed by a proof within 20 plies. The engine was not steering by
  build_score here, so the terms were not chosen by the policy.
- B: games with construction mode (grids 8-13). 26,000 games, 762,595
  positions, 4.7% positive. Confounded: the engine maximised the old score.

## Results (label y20)

```
                       A (no construction)   B (construction)
AUC hand weights              0.735               0.719
AUC fitted (same terms)       0.762               0.729
AUC fitted + new terms        0.766               0.744
```

Fitted weights on the build_score terms (boxed = 12), A / B, and the hand
weights:

```
term            hand     A      B
boxed            12     12     12
holes           -10     -8    -12
corner           25     47     48
edge (no corner) 10      6     -8
their_pieces      3      4      5
their_near        3    2.5      6
knight_prox       4     11    0.6
queen_prox        3     22     10
```

Both data sets agree: the corner is worth about twice the hand weight, a
plain edge is worth little, and the queen near the king matters far more.
New terms: a hole that our pieces cover costs about 3.5, an open one about
8.7 (holes -3.5, holes_open -5.2 in A), and a knight one move from a
checking square helps (+6). "Boxed" squares away from the edge predict
fewer proofs (mid_boxed -9).

`SmotherBuildVersion=2` uses: boxed 12, holes -4, open holes -6, corner 45,
plain edge 0, their pieces 4, near 4, knight 5 per step, queen 15 per step,
knight one hop from a check +5. Its spread on these positions is close to
the hand score (sd ratio 0.85-0.99), so SmotherBuildWeight keeps its meaning.
Its AUC is 0.766 on A but 0.716 on B, so the gain is only expected, not
shown: grid14 measures it in games.

## Where mates happen (mates.py)

```
opponent (grid)          full   all-but-one  4+ open   king at mate corner/edge/middle
Elo 1500 brutal (12)    10.8%      2.7%       40%      783 / 962 / 245
Maia 1100 brutal (12)    6.4%      5.9%       40%      287 / 586 / 127
Elo 3000 brutal (11)     1.3%      0.2%       70%      137 / 347 / 109
Elo 1500 default (5)     1.1%      3.9%       57%      311 / 1183 / 506
```

Across about 9,000 mates there were no full smothers in the middle of the
board and one "all but one": a king off the edge has 8 neighbours to fill.
At Elo 3000 the defending king escapes to open squares (70% of mates have 4
or more open squares) and only ~2% of games ever reach a proven smother.
