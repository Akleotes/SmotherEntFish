#!/usr/bin/env python3
"""Summarise match JSONL files; smothers are recounted by replaying the moves."""
import json, math, sys
import chess

def smother_kind(b):
    k = b.king(b.turn); checkers = b.checkers()
    for sq in chess.SquareSet(chess.BB_KING_ATTACKS[k]):
        if sq in checkers: continue
        pc = b.piece_at(sq)
        if not pc or pc.color != b.turn: return None
    return "classic" if any(b.piece_type_at(s) == chess.KNIGHT for s in checkers) else "any"

def open_squares(b):
    # Squares next to the mated king that are neither its own pieces nor the
    # checker's square: 0 = smother, 1 = "all but one" (SmotherPartial).
    k = b.king(b.turn); checkers = b.checkers(); n = 0
    for sq in chess.SquareSet(chess.BB_KING_ATTACKS[k]):
        if sq in checkers: continue
        pc = b.piece_at(sq)
        if not pc or pc.color != b.turn: n += 1
    return n

print(f"{'file':28} {'games':>5} {'W':>4} {'D':>4} {'L':>4} {'score':>6} {'+-95%':>6} "
      f"{'smoth':>5} {'class':>5} {'/100g':>6} {'/100W':>6} {'steer/g':>7} {'time':>4} "
      f"{'part':>4} {'s+p/100g':>8} {'ponder%':>7}")
for fn in sys.argv[1:]:
    gs = [json.loads(l) for l in open(fn)]
    n = len(gs); W = sum(g["ours"] == 1 for g in gs); D = sum(g["ours"] == .5 for g in gs); L = n - W - D
    sm = cl = part = 0
    for g in gs:
        if g["reason"] != "mate" or g["ours"] != 1: continue
        b = chess.Board(g["fen"])
        for m in g["moves"].split(): b.push_uci(m)
        k = smother_kind(b); sm += k is not None; cl += k == "classic"
        part += k is None and open_squares(b) == 1
    s = (W + D / 2) / n
    var = (W * (1 - s) ** 2 + D * (.5 - s) ** 2 + L * s ** 2) / n
    ci = 1.96 * math.sqrt(var / n)
    st = sum(g["steers"] for g in gs) / n
    tl = sum(g["reason"] == "time" for g in gs)
    ph = sum(g.get("ponder_hits", 0) for g in gs); pt = sum(g.get("ponder_total", 0) for g in gs)
    pond = f"{100*ph/pt:7.1f}" if pt else f"{'-':>7}"
    print(f"{fn.split('/')[-1]:28} {n:5} {W:4} {D:4} {L:4} {s:6.3f} {ci:6.3f} {sm:5} {cl:5} "
          f"{100*sm/n:6.1f} {100*sm/max(W,1):6.1f} {st:7.2f} {tl:4} "
          f"{part:4} {100*(sm+part)/n:8.1f} {pond}")
