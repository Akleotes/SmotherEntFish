#!/usr/bin/env python3
"""Make balanced 8-ply openings: each ply is a random pick among the stock
engine's top 4 at low depth; keep positions the engine scores within +-80 cp."""
import random, subprocess, sys
import chess

ENG, N, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]
p = subprocess.Popen([ENG], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
def send(s): p.stdin.write(s + "\n")
send("setoption name MultiPV value 4"); send("setoption name Threads value 4")

def search(fen, depth):
    send(f"position fen {fen}"); send(f"go depth {depth}")
    best = {}
    while True:
        l = p.stdout.readline().split()
        if l and l[0] == "bestmove": return best
        if "multipv" in l and "pv" in l and "score" in l:
            i = l.index("score")
            if l[i + 1] != "cp": continue
            best[int(l[l.index("multipv") + 1])] = (int(l[i + 2]), l[l.index("pv") + 1])

rnd = random.Random(7); seen = set(); out = []
while len(out) < N:
    b = chess.Board()
    for _ in range(8):
        lines = search(b.fen(), 6)
        if not lines: break
        b.push_uci(rnd.choice(list(lines.values()))[1])
    if b.ply() < 8 or b.fen() in seen: continue
    lines = search(b.fen(), 12)
    if 1 in lines and abs(lines[1][0]) <= 80:
        seen.add(b.fen()); out.append(b.fen())
open(OUT, "w").write("\n".join(out) + "\n")
send("quit")
print(len(out), "openings")
