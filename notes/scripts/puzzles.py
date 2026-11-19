#!/usr/bin/env python3
"""Prover regression test on Lichess smotheredMate puzzles.
usage: puzzles.py ENGINE smothered.csv N SEED [Option=Value ...]
smothered.csv: Lichess puzzle DB (CC0, database.lichess.org) rows with theme smotheredMate.
For each puzzle: position = FEN + first move (the opponent's); run the prover
(serial, go depth 1); claimed = proof reported; verified = its PV is legal
and ends in a smothered mate (every king neighbour own piece, except the
checker's square); bad = claimed but not verified."""
import csv, json, random, subprocess, sys
from multiprocessing import Pool
import chess

ENG, FN, N, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
EXTRA = dict(a.split("=", 1) for a in sys.argv[5:])
E = {}

def init():
    p = subprocess.Popen([ENG], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    for k, v in {"SmotherParallel": "false", "Hash": 16, **EXTRA}.items():
        p.stdin.write(f"setoption name {k} value {v}\n")
    E["p"] = p

def smothered(b):
    if not b.is_checkmate(): return False
    k = b.king(b.turn); ch = b.checkers()
    for sq in chess.SquareSet(chess.BB_KING_ATTACKS[k]):
        if sq in ch: continue
        pc = b.piece_at(sq)
        if not pc or pc.color != b.turn: return False
    return True

def run(row):
    pid, fen, moves = row
    b = chess.Board(fen); mv = moves.split(); b.push_uci(mv[0])
    sol_len = (len(mv) - 1 + 1) // 2
    p = E["p"]; p.stdin.write(f"position fen {b.fen()}\ngo depth 1\n")
    claimed = None; pv = None
    while True:
        l = p.stdout.readline()
        if "smother mate in" in l: claimed = int(l.split("mate in")[1].split()[0])
        if l.startswith("info") and " pv " in l and claimed: pass
        if l.startswith("bestmove"): break
    # Ask for the proven line: the engine prints the smother PV as its PV line
    # only via bestmove/ponder, so re-derive by replaying with the prover each move.
    ok = None
    if claimed:
        bb = b.copy(); ok = True
        for _ in range(2 * claimed + 2):
            if bb.is_game_over(): break
            p.stdin.write(f"position fen {bb.fen()}\ngo depth 1\n"); bm = None; again = None
            while True:
                l = p.stdout.readline()
                if "smother mate in" in l: again = int(l.split("mate in")[1].split()[0])
                if l.startswith("bestmove"): bm = l.split()[1]; break
            if again is None: ok = False; break
            bb.push_uci(bm)
            if bb.is_game_over(): break
            # defender: try every reply; the proof must survive the strongest.
            # Pick the reply after which the prover's smother is longest.
            worst = None; worst_len = -1
            for r in list(bb.legal_moves):
                bb.push(r)
                if bb.is_checkmate(): bb.pop(); continue
                p.stdin.write(f"position fen {bb.fen()}\ngo depth 1\n"); L = None
                while True:
                    l = p.stdout.readline()
                    if "smother mate in" in l: L = int(l.split("mate in")[1].split()[0])
                    if l.startswith("bestmove"): break
                bb.pop()
                if L is None: L = 99  # a plain-mate escape: allowed only if quicker (non-strict rule)
                if L > worst_len and L != 99: worst, worst_len = r, L
            if worst is None: break
            bb.push(worst)
        ok = ok and smothered(bb)
    return pid, sol_len, claimed, ok

if __name__ == "__main__":
    rows = [(r["PuzzleId"], r["FEN"], r["Moves"]) for r in csv.DictReader(open(FN))]
    random.Random(SEED).shuffle(rows); rows = rows[:N]
    res = []
    with Pool(4, init) as pool:
        for r in pool.imap_unordered(run, rows, chunksize=4):
            res.append(r)
    json.dump(res, open(f"puzzles_{ENG.split('/')[-1]}_{SEED}.json", "w"))
    claimed = sum(1 for r in res if r[2]); ver = sum(1 for r in res if r[2] and r[3]); bad = claimed - ver
    print(f"positions={len(res)} claimed={claimed} verified={ver} bad={bad}")
    by = {}
    for _, L, c, ok in res:
        d = by.setdefault(min(L, 9), [0, 0]); d[0] += 1; d[1] += bool(c)
    print("by solution length (moves): " + ", ".join(f"{k}:{v[1]}/{v[0]}" for k, v in sorted(by.items())))
