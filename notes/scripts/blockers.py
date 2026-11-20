#!/usr/bin/env python3
"""Blocker diagnostics for match JSONL files (see notes/HANDOFF.md, "Blocker
starvation").

usage: blockers.py GAMES.jsonl...

Per file: smothers (full, near) per 100 games; games with a proof
(the prover found a forced smother at least once), how many of them were
delivered; and for delivered vs escaped proof games the defender's pieces
(non-king) and blocker reserve (pieces minus empty or attacked king-ring
squares) at the first proof, our captures after it, and the defender's
pieces at the end.
"""
import json, os, statistics as st, sys
import chess



def open_squares(b):
    # Squares next to the mated king that are neither its own pieces nor the
    # checker's square (as in summary.py): 0 = smother, 1 = "all but one".
    k = b.king(b.turn); checkers = b.checkers(); n = 0
    for sq in chess.SquareSet(chess.BB_KING_ATTACKS[k]):
        if sq in checkers: continue
        pc = b.piece_at(sq)
        if not pc or pc.color != b.turn: n += 1
    return n


def defender_info(b, them):
    k = b.king(them)
    pieces = chess.popcount(b.occupied_co[them]) - 1
    ring = chess.SquareSet(chess.BB_KING_ATTACKS[k])
    holes = sum(1 for s in ring if b.color_at(s) != them)
    return pieces, pieces - holes


def med(v):
    return f"{st.median(v):4.1f}" if v else "   -"


for fn in sys.argv[1:]:
    G = [json.loads(l) for l in open(fn)]
    full = near = 0
    rows = {"delivered": [], "escaped": []}
    for g in G:
        b = chess.Board(g["fen"])
        us = chess.WHITE if g["ours_white"] else chess.BLACK
        them = not us
        moves = g["moves"].split()
        first = min(g["proofs"]) if g.get("proofs") else None
        at_proof = None
        caps = 0
        for i, m in enumerate(moves):
            if first is not None and i == first:
                at_proof = defender_info(b, them)
            mv = chess.Move.from_uci(m)
            if first is not None and i >= first and b.turn == us and b.is_capture(mv):
                caps += 1
            b.push(mv)
        mate = b.is_checkmate() and b.turn == them
        k = mate and open_squares(b) == 0
        full += bool(k)
        near += mate and open_squares(b) == 1
        if first is not None and at_proof:
            end = chess.popcount(b.occupied_co[them]) - 1
            rows["delivered" if k else "escaped"].append((at_proof[0], at_proof[1], caps, end))
    n = len(G)
    d, e = rows["delivered"], rows["escaped"]
    pg = len(d) + len(e)
    print(f"{os.path.basename(fn)}: {n} games, full {100*full/n:.1f}/100, near {100*near/n:.1f}/100, "
          f"proof games {100*pg/n:.1f}/100, delivered {100*len(d)/max(1,pg):.0f}%")
    for name, r in rows.items():
        if r:
            print(f"  {name:9s} n={len(r):4d}  at proof: pieces {med([x[0] for x in r])} reserve {med([x[1] for x in r])}"
                  f"  our captures after {med([x[2] for x in r])}  pieces at end {med([x[3] for x in r])}")
