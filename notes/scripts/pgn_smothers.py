#!/usr/bin/env python3
"""Count results and smothered mates in PGN files (Lichess bot games).

usage: pgn_smothers.py BOTNAME FILE_OR_DIR...

A game ending in mate by BOTNAME is a full smother when every square next
to the mated king (except the checker's) holds one of its own pieces, near
("all but one") when one such square is not.
"""
import os, sys
import chess, chess.pgn

me = sys.argv[1].lower()
files = []
for a in sys.argv[2:]:
    files += [os.path.join(a, f) for f in sorted(os.listdir(a)) if f.endswith(".pgn")] if os.path.isdir(a) else [a]


def open_squares(b):
    k = b.king(b.turn); ch = b.checkers(); n = 0
    for s in chess.SquareSet(chess.BB_KING_ATTACKS[k]):
        if s in ch:
            continue
        p = b.piece_at(s)
        if not p or p.color != b.turn:
            n += 1
    return n


rows = []
for fn in files:
    with open(fn) as f:
        while (g := chess.pgn.read_game(f)) is not None:
            h = g.headers
            white = h.get("White", "").lower() == me
            b = g.end().board()
            res = h.get("Result", "*")
            ours = {"1-0": 1.0, "0-1": 0.0}.get(res, 0.5) if white else {"1-0": 0.0, "0-1": 1.0}.get(res, 0.5)
            kind = ""
            if b.is_checkmate() and b.turn == (chess.BLACK if white else chess.WHITE):
                n = open_squares(b)
                kind = "FULL" if n == 0 else "near" if n == 1 else "mate"
            opp = h.get("Black" if white else "White", "?")
            orating = h.get("BlackElo" if white else "WhiteElo", "?")
            rows.append((ours, kind, opp, orating, h.get("TimeControl", "?"), h.get("Site", "")))

w = sum(r[0] == 1 for r in rows); d = sum(r[0] == 0.5 for r in rows); l = sum(r[0] == 0 for r in rows)
full = sum(r[1] == "FULL" for r in rows); near = sum(r[1] == "near" for r in rows)
print(f"{len(rows)} games: +{w} ={d} -{l}; smothers: {full} full, {near} near")
for r in rows:
    print(f"  {'W' if r[0]==1 else 'D' if r[0]==0.5 else 'L'} {r[1]:4} vs {r[2]} ({r[3]}) {r[4]} {r[5]}")
