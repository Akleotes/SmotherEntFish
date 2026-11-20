#!/usr/bin/env python3
"""Merge pentanomial counts from parallel fastchess runs and compute the SPRT.

usage: sprt_stats.py ELO0 ELO1 ALPHA BETA FILE.json [...]
Each FILE.json holds {"ptnml": [p0, p1, p2, p3, p4]}: counts of game pairs
(same opening, colours swapped) scoring 0, 0.5, 1, 1.5, 2 points for the
new engine. Prints one JSON line: totals, Elo estimate with a 95% interval,
the log-likelihood ratio and the verdict ("H1" = new engine is at least ELO1
better, "H0" = at most ELO0, "continue").

The test is the generalized SPRT on pair scores, as used by fishtest:
LLR = N * (s1 - s0) * (2*m - s0 - s1) / (2 * var), where m and var are the
mean and variance of the pair score (scaled to 0..1) and s0, s1 the expected
scores at ELO0 and ELO1 (logistic Elo). Bounds: log(beta/(1-alpha)) and
log((1-beta)/alpha).
"""
import json
import math
import sys


def score_of(elo):
    return 1 / (1 + 10 ** (-elo / 400))


def elo_of(score):
    score = min(max(score, 1e-6), 1 - 1e-6)
    return -400 * math.log10(1 / score - 1)


def sprt(ptnml, elo0, elo1, alpha, beta):
    n = sum(ptnml)
    if n == 0:
        return {"pairs": 0, "llr": 0.0, "verdict": "continue"}
    vals = [0, 0.25, 0.5, 0.75, 1]
    m = sum(v * c for v, c in zip(vals, ptnml)) / n
    var = sum(c * (v - m) ** 2 for v, c in zip(vals, ptnml)) / n
    var = max(var, 1e-9)
    s0, s1 = score_of(elo0), score_of(elo1)
    llr = n * (s1 - s0) * (2 * m - s0 - s1) / (2 * var)
    lo, hi = math.log(beta / (1 - alpha)), math.log((1 - beta) / alpha)
    se = math.sqrt(var / n)
    verdict = "H1" if llr >= hi else "H0" if llr <= lo else "continue"
    return {"pairs": n, "games": 2 * n, "ptnml": ptnml, "score": round(m, 4),
            "elo": round(elo_of(m), 1),
            "elo_95": [round(elo_of(m - 1.96 * se), 1), round(elo_of(m + 1.96 * se), 1)],
            "llr": round(llr, 3), "bounds": [round(lo, 3), round(hi, 3)], "verdict": verdict}


if __name__ == "__main__":
    elo0, elo1, alpha, beta = (float(x) for x in sys.argv[1:5])
    total = [0] * 5
    for fn in sys.argv[5:]:
        p = json.load(open(fn))["ptnml"]
        total = [a + b for a, b in zip(total, p)]
    print(json.dumps(sprt(total, elo0, elo1, alpha, beta)))
