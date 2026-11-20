"""How far from a smother were our mates, and how do decided games run?

usage: mates.py FILE.jsonl [...]
Prints, over games we won by mate: the distribution of 'open' squares around
the mated king (neighbours that are neither its own pieces nor the checker's
square): 0 = smother (AnyPiece), 1 = 'all but one' (item 3), and where the
king stood. Also, for decided games, plies from first +8 material to mate and
how many had a proof.
"""
import json
import sys
from collections import Counter

import chess

VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}


def open_squares(b):
    k = b.king(b.turn)
    ch = b.checkers()
    n = 0
    for s in chess.SquareSet(chess.BB_KING_ATTACKS[k]):
        if s in ch:
            continue
        pc = b.piece_at(s)
        if not pc or pc.color != b.turn:
            n += 1
    f, r = chess.square_file(k), chess.square_rank(k)
    where = "corner" if f in (0, 7) and r in (0, 7) else "edge" if f in (0, 7) or r in (0, 7) else "middle"
    return n, where


for path in sys.argv[1:]:
    opens = Counter(); where = Counter(); open_where = Counter()
    wins = mates = 0; dur = []; proofgames = 0; decided = 0; plies_after = []
    for line in open(path):
        g = json.loads(line)
        if "moves" not in g or g.get("ours") != 1.0:
            continue
        wins += 1
        us = chess.WHITE if g["ours_white"] else chess.BLACK
        b = chess.Board(g["fen"]); first = None
        for i, u in enumerate(g["moves"].split()):
            if first is None:
                mat = sum(VAL[p.piece_type] * (1 if p.color == us else -1) for p in b.piece_map().values())
                if mat >= 8:
                    first = i
            b.push_uci(u)
        if first is not None:
            decided += 1; plies_after.append(len(g["moves"].split()) - first)
        if g.get("proofs"):
            proofgames += 1
        if g.get("reason") == "mate":
            mates += 1
            n, w = open_squares(b)
            opens[min(n, 4)] += 1; where[w] += 1; open_where[(min(n, 2), w)] += 1
    plies_after.sort()
    med = plies_after[len(plies_after) // 2] if plies_after else 0
    print(f"{path.split('__')[-1]}: wins={wins} mates={mates} decided(+8)={decided} "
          f"median plies after +8={med} games with a proof={proofgames}")
    print("   open squares at mate: " + "  ".join(f"{k}:{opens[k]} ({100*opens[k]/max(mates,1):.1f}%)" for k in range(5)))
    print("   king at mate: " + "  ".join(f"{w}:{where[w]}" for w in ("corner", "edge", "middle")))
    print("   open<=1 by place: " + "  ".join(f"{w}: full {open_where[(0, w)]} / all-but-one {open_where[(1, w)]}"
                                         for w in ("corner", "edge", "middle")))
