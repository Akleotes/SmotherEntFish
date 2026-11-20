"""Fit build_score weights against 'a proven smother follows within 20 plies'.

usage: fit.py DATA.npz [label]   label: y20 (default) or ys
"""
import sys

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

d = np.load(sys.argv[1])
label = sys.argv[2] if len(sys.argv) > 2 else "y20"
X, y, g, names = d["X"], d[label], d["g"], list(d["names"])
ix = {n: i for i, n in enumerate(names)}
print(f"{sys.argv[1]} label={label} positions={len(y)} positives={y.sum()} ({100*y.mean():.2f}%) games={len(set(g))}")

# The engine's current score (src/smother.cpp build_score, survivability off).
cur_w = {"boxed": 12, "holes": -10, "corner": 25, "edge": 10, "their_pieces": 3,
         "their_near": 3, "knight_prox": 4, "queen_prox": 3}
# build_score adds 10 for an edge and 25 for a corner, not both.
def current(X):
    s = np.zeros(len(X))
    for n, w in cur_w.items():
        if n == "edge":
            s += w * X[:, ix["edge"]] * (1 - X[:, ix["corner"]])
        else:
            s += w * X[:, ix[n]]
    return s

print(f"AUC current hand weights: {roc_auc_score(y, current(X)):.3f}")
for n in names:
    a = roc_auc_score(y, X[:, ix[n]])
    print(f"  single {n:14s} AUC {a:.3f}  mean pos {X[y==1, ix[n]].mean():6.2f}  neg {X[y==0, ix[n]].mean():6.2f}")

def cv_fit(cols, tag):
    Xs = X[:, [ix[c] for c in cols]]
    aucs = []
    for tr, te in GroupKFold(n_splits=5).split(Xs, y, g):
        sc = StandardScaler().fit(Xs[tr])
        m = LogisticRegression(max_iter=2000, C=1.0).fit(sc.transform(Xs[tr]), y[tr])
        aucs.append(roc_auc_score(y[te], m.predict_proba(sc.transform(Xs[te]))[:, 1]))
    sc = StandardScaler().fit(Xs)
    m = LogisticRegression(max_iter=2000, C=1.0).fit(sc.transform(Xs), y)
    raw = m.coef_[0] / sc.scale_  # per raw unit
    scale = 12 / raw[cols.index("boxed")] if "boxed" in cols and raw[cols.index("boxed")] > 0 else 1
    print(f"\n{tag}: CV AUC {np.mean(aucs):.3f} +- {np.std(aucs):.3f}")
    print("  term            std.coef   raw/unit   as build_score weight (boxed = 12)")
    for c, sc_, r in zip(cols, m.coef_[0], raw):
        print(f"  {c:14s} {sc_:9.3f} {r:10.4f} {r*scale:10.1f}")

base = ["boxed", "holes", "corner", "edge", "their_pieces", "their_near", "knight_prox", "queen_prox"]
cv_fit(base, "fitted, build_score terms only")
cv_fit(base + ["mid_boxed", "holes_covered", "holes_open", "knight_hop", "their_moves"], "fitted, plus candidate terms")
cv_fit(base + ["mid_boxed", "holes_covered", "holes_open", "knight_hop", "their_moves", "material"], "fitted, plus candidate terms and material")
