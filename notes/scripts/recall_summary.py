#!/usr/bin/env python3
"""Summary of recall.py output. usage: recall_summary.py RECALL.jsonl..."""
import json, statistics as st, sys

R = [json.loads(l) for f in sys.argv[1:] for l in open(f)]
n = len(R)


def med(v):
    return f"{st.median(v):.0f}" if v else "-"


def pct(k):
    return f"{100 * k / max(n, 1):5.1f}%"


C = {}
for r in R:
    C.setdefault(r["cls"], []).append(r)
print(f"{n} won games (ours == 1.0)")
for c, txt in (("full", "true smother delivered"),
               ("missed", "forced true smother existed, engine claimed no proof there"),
               ("unconverted", "engine claimed a proof there, no true smother followed"),
               ("never", "no forced true smother in any winning position checked")):
    k = len(C.get(c, []))
    print(f"  {c:12s} {k:5d} {pct(k)}  {txt}")

av = [r for r in R if r.get("avail") is not None]
print(f"\nforced true smother available at some point: {len(av)} ({pct(len(av))})")
if av:
    print(f"  mate-in at first availability: median {med([r['mate_in'] for r in av])}, "
          f"<=4: {sum(r['mate_in'] <= 4 for r in av)}, 5-8: {sum(5 <= r['mate_in'] <= 8 for r in av)}, "
          f">8: {sum(r['mate_in'] > 8 for r in av)}")
    sf = [r for r in av if "small_finds" in r]
    print(f"  normal prover limits (8 moves, 1 quiet, 5M) also find it: "
          f"{sum(r['small_finds'] for r in sf)} of {len(sf)}")
    ev = [r["eval_at_avail"] for r in av if r.get("eval_at_avail") is not None]
    print(f"  eval at availability (cp, mate=100000): median {med(ev)}, "
          f">=1000 or mate: {sum(e >= 1000 for e in ev)} of {len(ev)}")
    print(f"  plies from first winning position to availability: median "
          f"{med([r['avail'] - r['first_win'] for r in av if r.get('first_win') is not None])}")

for c in ("missed", "unconverted"):
    G = C.get(c, [])
    if G:
        later = sum(any(p > r["avail"] for p in r["proofs"]) for r in G)
        near = sum(r.get("open") == 1 for r in G)
        print(f"\n{c}: {len(G)} games; engine proof later in the game: {later}; "
              f"ended in a near smother: {near}; small limits find it: "
              f"{sum(r.get('small_finds', False) for r in G)}")

G = C.get("never", [])
if G:
    print(f"\nnever: {len(G)} games; ended in a near smother: {sum(r.get('open') == 1 for r in G)}; "
          f"winning positions checked per game: median {med([r['checked'] for r in G])}")
    print(f"  defender pieces (non-king) at first winning position: median "
          f"{med([r['pieces_at_win'] for r in G if 'pieces_at_win' in r])} "
          f"(full games: {med([r['pieces_at_win'] for r in C.get('full', []) if 'pieces_at_win' in r])})")
    print(f"  plies from first winning position to the end: median "
          f"{med([r['plies'] - r['first_win'] for r in G if r.get('first_win') is not None])}")
print(f"\nCPU seconds per game: median {med([r['secs'] for r in R])}")
