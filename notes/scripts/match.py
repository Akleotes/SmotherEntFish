#!/usr/bin/env python3
"""Minimal paired-game match runner (stand-in for fastchess, which we cannot fetch here).

usage: match.py OUT.jsonl OURS OPP ELO GAMES [--steer N] [--opt Name=Value ...]
        [--tc 5+0.05] [--conc 4] [--book openings.txt]

Each opening is played twice with colours swapped. Clocks are real: a side
whose move takes longer than its remaining time (+ 100 ms grace) loses.
Smothered mate = checkmate where every square next to the mated king is
held by its own pieces or off the board; "classic" if the checker is a knight.
"""
import argparse, json, os, random, subprocess, sys, time
from multiprocessing import Pool
import chess

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("ours"); ap.add_argument("opp")
ap.add_argument("elo", type=int); ap.add_argument("games", type=int)
ap.add_argument("--opt", action="append", default=[])
ap.add_argument("--tc", default="5+0.05"); ap.add_argument("--conc", type=int, default=4)
ap.add_argument("--book", default=os.path.join(os.path.dirname(__file__), "openings.txt"))
ap.add_argument("--seed", type=int, default=1)
# Custom opponent (e.g. Maia on lc0): its own UCI options, and a fixed "go"
# command instead of a clock (Maia plays like a human with "go nodes 1").
# With --opp-opt given, the UCI_Elo limit is not applied to the opponent.
ap.add_argument("--opp-opt", action="append", default=[])
ap.add_argument("--opp-go", default="")
A = ap.parse_args()
BASE, INC = (float(x) for x in A.tc.split("+"))


class Eng:
    def __init__(self, path, opts):
        self.p = subprocess.Popen([path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.send("uci"); self.wait("uciok")
        for k, v in opts.items():
            self.send(f"setoption name {k} value {v}")
        self.ready()

    def send(self, s): self.p.stdin.write(s + "\n")
    def wait(self, tok):
        while True:
            l = self.p.stdout.readline()
            if not l: raise RuntimeError("engine died")
            if l.startswith(tok): return l
    def ready(self): self.send("isready"); self.wait("readyok")

    def go(self, fen, moves, wt, bt, fixed=""):
        self.send(f"position fen {fen} moves {' '.join(moves)}" if moves else f"position fen {fen}")
        self.send(f"go {fixed}" if fixed else
                  f"go wtime {int(wt*1000)} btime {int(bt*1000)} winc {int(INC*1000)} binc {int(INC*1000)}")
        t0 = time.monotonic(); infos = []
        while True:
            l = self.p.stdout.readline()
            if not l: raise RuntimeError("engine died")
            if l.startswith("info string"): infos.append(l.strip())
            elif l.startswith("bestmove"):
                return l.split()[1], time.monotonic() - t0, infos

    def quit(self):
        try: self.send("quit"); self.p.wait(2)
        except Exception: self.p.kill()


def smother_kind(b):
    """Called on a checkmated board (side to move is mated)."""
    # Matches the engine's AnyPiece style: every square next to the king holds
    # one of its own pieces, except the checking piece's own square.
    k = b.king(b.turn)
    checkers = b.checkers()
    for sq in chess.SquareSet(chess.BB_KING_ATTACKS[k]):
        if sq in checkers:
            continue
        pc = b.piece_at(sq)
        if not pc or pc.color != b.turn:
            return None
    if any(b.piece_type_at(s) == chess.KNIGHT for s in checkers):
        return "classic"
    return "any"


ENGS = {}
def worker_init(opts_ours, opts_opp):
    ENGS["ours"] = Eng(A.ours, opts_ours)
    ENGS["opp"] = Eng(A.opp, opts_opp)


def play(job):
    gi, fen0, ours_white = job
    ours, opp = ENGS["ours"], ENGS["opp"]
    for e in (ours, opp):
        e.send("ucinewgame"); e.ready()
    b = chess.Board(fen0)
    moves, clock = [], {chess.WHITE: BASE, chess.BLACK: BASE}
    steers = 0; steer_plies = []; result = None; reason = ""
    while result is None:
        stm = b.turn
        is_ours = (stm == chess.WHITE) == ours_white
        e = ours if is_ours else opp
        fixed = "" if is_ours else A.opp_go
        mv, dt, infos = e.go(fen0, moves, clock[chess.WHITE], clock[chess.BLACK], fixed)
        if fixed:
            dt = 0  # a fixed-node opponent plays without a clock
        if is_ours:
            for i in infos:
                if "smother steer" in i:
                    steers += 1; steer_plies.append(len(moves))
        clock[stm] -= dt
        if clock[stm] < -0.1:
            result = "0-1" if stm == chess.WHITE else "1-0"; reason = "time"; break
        clock[stm] += INC
        try:
            m = chess.Move.from_uci(mv)
            if m not in b.legal_moves: raise ValueError
        except Exception:
            result = "0-1" if stm == chess.WHITE else "1-0"; reason = f"illegal {mv}"; break
        b.push(m); moves.append(mv)
        if b.is_checkmate():
            result = "1-0" if b.turn == chess.BLACK else "0-1"; reason = "mate"
        elif b.is_stalemate() or b.is_insufficient_material() or b.can_claim_draw():
            result = "1/2-1/2"; reason = "draw"
        elif len(moves) >= 400:
            result = "1/2-1/2"; reason = "cap"
    sm = smother_kind(b) if reason == "mate" else None
    ours_score = {"1-0": 1.0, "0-1": 0.0}.get(result, 0.5)
    if not ours_white: ours_score = 1.0 - ours_score
    ours_mated_them = reason == "mate" and ours_score == 1.0
    return {"game": gi, "fen": fen0, "ours_white": ours_white, "result": result,
            "reason": reason, "ours": ours_score, "plies": len(moves),
            "smother": sm if ours_mated_them else None,
            "smothered_us": sm if (reason == "mate" and ours_score == 0.0) else None,
            "steers": steers, "steer_plies": steer_plies, "moves": " ".join(moves)}


def parse_opts(lst):
    d = {}
    for s in lst:
        k, v = s.split("=", 1); d[k] = v
    return d


if __name__ == "__main__":
    book = [l.strip() for l in open(A.book) if l.strip()]
    rnd = random.Random(A.seed); rnd.shuffle(book)
    jobs = []
    for r in range(A.games // 2):
        fen = book[r % len(book)]
        jobs += [(2 * r, fen, True), (2 * r + 1, fen, False)]
    ours_opts = {"Threads": 1, "Hash": 16, **parse_opts(A.opt)}
    opp_opts = ({"Threads": 1, **parse_opts(A.opp_opt)} if A.opp_opt else
                {"Threads": 1, "Hash": 16, "UCI_LimitStrength": "true", "UCI_Elo": A.elo})
    W = D = L = SM = SMC = ST = 0
    with Pool(A.conc, worker_init, (ours_opts, opp_opts)) as pool, open(A.out, "a") as f:
        for n, g in enumerate(pool.imap_unordered(play, jobs), 1):
            f.write(json.dumps(g) + "\n"); f.flush()
            W += g["ours"] == 1; D += g["ours"] == 0.5; L += g["ours"] == 0
            SM += g["smother"] is not None; SMC += g["smother"] == "classic"; ST += g["steers"]
            if n % 20 == 0 or n == len(jobs):
                print(f"{n}/{len(jobs)} W{W} D{D} L{L} score {(W+D/2)/n:.3f} "
                      f"smothers {SM} (classic {SMC}) steers {ST}", flush=True)
