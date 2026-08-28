#!/usr/bin/env python3
"""Self-test for price_models.py against panels with a KNOWN answer.

WHY THIS FILE WAS REWRITTEN
---------------------------
The first version of this test passed while the estimator was wrong, which is
the worst thing a test can do. It generated the price series as an INDEPENDENT
variable and then set revenue = price x units. Real panels do the opposite:
there is no price column in PDI, so price is DERIVED as revenue / units. That
one difference is the entire bug.

When price = r/q, then ln p = ln r - ln q. Any measurement error u in quantity -
counting noise, store composition inside the cell, multibuy deals recorded
unevenly - enters the left-hand side of a volume-on-price regression as +u and
the right-hand side as -u. The estimator converges to

    plim(beta_hat) = ( beta * Var(ln p*) - Var(u) ) / ( Var(ln p*) + Var(u) )

which is negative even when beta is exactly zero. No fixed effect removes it,
because it is not an omitted variable: it is the same measurement appearing
twice with opposite signs.

The old generator could never produce that, so it certified a biased estimator
at -1.498 against a planted -1.50. This version derives price the way the real
pipeline does, and additionally builds two disjoint store halves so the
cross-half estimator can be checked.

WHAT IS ASSERTED
----------------
Case A, TRUE ELASTICITY EXACTLY ZERO. The naive estimator must print a clearly
negative number - that is the artifact, reproduced on demand - and the
cross-half estimator must stay near zero. This is the test that would have
caught the original bug.

Case B, TRUE ELASTICITY NEGATIVE. The two estimators must BRACKET the truth:
naive inflated away from zero by division bias, cross-half attenuated toward
zero by classical measurement error in the regressor. That bracket is exactly
what price_models.py claims to report, so the test asserts the claim rather
than a single number.

Deterministic LCG, no clock-seeded randomness, so a failure is a regression.

    python data/scripts/test_price_models.py

stdlib only. Exits non-zero on failure.
"""
import csv
import math
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

# sd of the true log price, and of the quantity measurement error. Both chosen
# so the artifact is unmistakable without being absurd: the implied naive bias
# at beta=0 is -Var(u)/(Var(p*)+Var(u)) = -0.004/0.0104 = -0.385.
SD_LOG_PRICE = 0.08
SD_NOISE = 0.0632          # Var(u) = 0.004


def lcg(seed):
    state = [seed]

    def rnd():
        state[0] = (1103515245 * state[0] + 12345) % (2 ** 31)
        return state[0] / 2 ** 31
    return rnd


def gauss(rnd):
    """Box-Muller from the LCG. Two uniforms in, one standard normal out."""
    u1 = max(1e-12, rnd())
    u2 = rnd()
    return math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)


def make_panel(path, beta, seed=4242):
    """Panel where price is DERIVED as revenue/units, exactly as the real
    pipeline derives it, with independent measurement error in each store half."""
    rnd = lcg(seed)
    months = [f"{y}-{m:02d}" for y in range(2019, 2026) for m in range(1, 13)]
    families = ["Original", "Berry", "Citrus", "Tropical",
                "Watermelon", "Sour & candy", "Grape", "Coffee & cream"]
    rows = []
    for ci, cluster in enumerate(families):
        base = 2_000_000 * (1 + ci)
        for t, m in enumerate(months):
            moy = int(m[5:7])
            season = 0.12 * math.sin(2 * math.pi * (moy - 3) / 12)
            stores = 30000 + 60 * t

            # TRUE price and TRUE quantity. The elasticity lives here and
            # nowhere else.
            log_p_true = SD_LOG_PRICE * gauss(rnd)
            p_true = 2.90 * math.exp(log_p_true)
            q_true = base * math.exp(beta * log_p_true + season
                                     + 0.35 * math.log(stores / 30000))

            # Two disjoint halves of stores. Revenue is recorded exactly;
            # quantity is recorded with independent noise in each half. That is
            # the asymmetry that creates division bias when price is r/q.
            qa_true, qb_true = q_true / 2, q_true / 2
            ua, ub = SD_NOISE * gauss(rnd), SD_NOISE * gauss(rnd)
            units_a = qa_true * math.exp(ua)
            units_b = qb_true * math.exp(ub)
            rev_a, rev_b = p_true * qa_true, p_true * qb_true

            units = units_a + units_b
            rev = rev_a + rev_b
            price_a = rev_a / units_a       # = p_true * exp(-ua)
            price_b = rev_b / units_b       # = p_true * exp(-ub)
            price = rev / units             # the contaminated series

            rows.append({
                "scheme": "family", "cluster": cluster, "month": m,
                "rev": round(rev, 2), "units": round(units), "skus": 40,
                "stores": int(stores),
                "price_unitvalue": round(price, 5),
                # price_index is what the naive specifications regress on, and
                # in the real pipeline it is built from these same r/q ratios.
                "price_index": round(price / 2.90, 6),
                "matched_share": 0.9,
                "price_index_a": round(price_a / 2.90, 6),
                "price_index_b": round(price_b / 2.90, 6),
                "matched_share_a": 0.9, "matched_share_b": 0.9,
                "units_a": round(units_a), "units_b": round(units_b),
                "disc_rate": 0.08, "disc_txn_rate": 0.07,
            })
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def run(path):
    out = subprocess.run(
        [sys.executable, os.path.join(HERE, "price_models.py"), "--panel", path],
        capture_output=True, text=True, timeout=900)
    if out.returncode != 0:
        print(out.stdout, out.stderr)
        sys.exit("price_models.py exited non-zero")
    return out.stdout


def grab(text, label):
    for line in text.splitlines():
        if label in line:
            for tok in line.replace("<-", " ").split():
                try:
                    return float(tok.replace("+", ""))
                except ValueError:
                    continue
    return None


def main():
    fails = []
    with tempfile.TemporaryDirectory() as tmp:
        # ---- Case A: the truth is ZERO. Any negative number is the artifact --
        pa = os.path.join(tmp, "zero.csv")
        n = make_panel(pa, beta=0.0)
        ta = run(pa)
        naive = grab(ta, "within + distribution + season")
        cross = grab(ta, "mean  ") or grab(ta, "    mean")
        print(f"CASE A  true elasticity 0.0  ({n} cluster-months)")
        print(f"  naive (price = revenue/units)   {naive}")
        print(f"  cross-half                      {cross}")
        if naive is None or naive > -0.15:
            fails.append(f"naive estimator returned {naive} on a zero-elasticity "
                         "panel — the test is not reproducing division bias, so it "
                         "cannot certify the fix")
        if cross is None:
            fails.append("no cross-half estimate produced")
        elif abs(cross) > 0.12:
            fails.append(f"cross-half returned {cross} on a zero-elasticity panel; "
                         "it should be near zero")

        # ---- Case B: a real negative elasticity. The two must bracket it -----
        pb = os.path.join(tmp, "neg.csv")
        make_panel(pb, beta=-0.80, seed=99)
        tb = run(pb)
        naive_b = grab(tb, "within + distribution + season")
        cross_b = grab(tb, "mean  ") or grab(tb, "    mean")
        print(f"\nCASE B  true elasticity -0.80")
        print(f"  naive                           {naive_b}")
        print(f"  cross-half                      {cross_b}")
        if None in (naive_b, cross_b):
            fails.append("case B did not produce both estimates")
        else:
            if not naive_b < -0.80:
                fails.append(f"naive {naive_b} was not inflated away from zero "
                             "relative to the planted -0.80")
            if not cross_b > -0.80:
                fails.append(f"cross-half {cross_b} was not attenuated toward zero "
                             "relative to the planted -0.80")
            if not (cross_b > naive_b):
                fails.append("the two estimators did not bracket the truth")
            print(f"  bracket: [{naive_b}, {cross_b}] contains -0.80 = "
                  f"{naive_b < -0.80 < cross_b}")

    if fails:
        print("\nFAILED:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("\nall assertions passed")


if __name__ == "__main__":
    main()
