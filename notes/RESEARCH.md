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
