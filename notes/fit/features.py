"""Extract build_score features from decided positions in match records.

usage: features.py OUT.npz FILE.jsonl [...]

For every game, replay the moves. At each position where we are to move and
lead by >= MATLEAD pawns of material, record the build_score terms (mirroring
src/smother.cpp build_score) plus candidate terms, and labels:
  y_proof20 : the prover proved a smother within the next 20 plies
  y_smother : the game ended in a smother we delivered
"""
import json
import sys
from multiprocessing import Pool

import chess
import numpy as np

MATLEAD = 8
VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}

NAMES = [
    # build_score terms
    "boxed", "holes", "corner", "edge", "their_pieces", "their_near",
    "knight_prox", "queen_prox",
    # candidate terms
    "mid_boxed",       # boxed squares when the king is off the edge
    "holes_covered",   # holes attacked by our pieces (partial smother)
    "holes_open",      # holes neither theirs nor attacked by us
    "knight_hop",      # our knights one move from a checking square
    "material",        # our material lead in pawns
    "their_moves",     # legal moves for them if it were their turn
]


def dist(a, b):
    return max(abs(chess.square_file(a) - chess.square_file(b)), abs(chess.square_rank(a) - chess.square_rank(b)))


def features(b, us):
    them = not us
    k = b.king(them)
    ring = chess.SquareSet(chess.BB_KING_ATTACKS[k])
    theirs = b.occupied_co[them]
    boxed = sum(1 for s in ring if theirs & chess.BB_SQUARES[s])
    holes_sq = [s for s in ring if not theirs & chess.BB_SQUARES[s]]
    holes = len(holes_sq)
    f, r = chess.square_file(k), chess.square_rank(k)
    corner = int(f in (0, 7) and r in (0, 7))
    edge = int(f in (0, 7) or r in (0, 7))
    pieces = [s for s in chess.SquareSet(theirs) if s != k]
    near = sum(1 for s in pieces if dist(s, k) <= 2)
    kn = sum(max(0, 4 - dist(s, k)) for s in b.pieces(chess.KNIGHT, us))
    qn = sum(max(0, 4 - dist(s, k)) for s in b.pieces(chess.QUEEN, us))
    covered = sum(1 for s in holes_sq if b.is_attacked_by(us, s))
    checks = chess.SquareSet(chess.BB_KNIGHT_ATTACKS[k]) - chess.SquareSet(b.occupied_co[us])
    hop = 0
    for s in b.pieces(chess.KNIGHT, us):
        if chess.SquareSet(chess.BB_KNIGHT_ATTACKS[s]) & checks:
            hop += 1
    mat = sum(VAL[p.piece_type] * (1 if p.color == us else -1) for p in b.piece_map().values())
    bb = b.copy(stack=False)
    bb.turn = them
    bb.ep_square = None
    nmoves = bb.legal_moves.count() if not bb.is_check() else 0
    return [boxed, holes, corner, edge, len(pieces), near, kn, qn,
            boxed * (1 - edge), covered, holes - covered, hop, mat, nmoves]


def game_rows(line):
    try:
        g = json.loads(line)
    except Exception:
        return []
    if not g.get("moves"):
        return []
    us = chess.WHITE if g["ours_white"] else chess.BLACK
    proofs = g.get("proofs") or []
    smother = 1 if g.get("smother") and g.get("ours") == 1.0 else 0
    b = chess.Board(g["fen"])
    rows = []
    for ply, u in enumerate(g["moves"].split()):
        if b.turn == us and not b.is_check():
            mat = sum(VAL[p.piece_type] * (1 if p.color == us else -1) for p in b.piece_map().values())
            if mat >= MATLEAD:
                y20 = int(any(ply <= p < ply + 20 for p in proofs))
                rows.append((features(b, us), y20, smother))
        try:
            b.push_uci(u)
        except Exception:
            break
    return rows


def main():
    out = sys.argv[1]
    lines = []
    gid = []
    for i, path in enumerate(sys.argv[2:]):
        with open(path) as fh:
            for line in fh:
                lines.append(line)
                gid.append(len(gid))
    with Pool(4) as pool:
        res = pool.map(game_rows, lines, chunksize=50)
    X, Y20, YS, G = [], [], [], []
    for g, rows in zip(gid, res):
        for x, y20, ys in rows:
            X.append(x); Y20.append(y20); YS.append(ys); G.append(g)
    np.savez_compressed(out, X=np.array(X, dtype=np.float32), y20=np.array(Y20), ys=np.array(YS),
                        g=np.array(G), names=np.array(NAMES))
    print(f"games={len(lines)} positions={len(X)} proof20={sum(Y20)} smother_pos={sum(YS)}")


if __name__ == "__main__":
    main()
