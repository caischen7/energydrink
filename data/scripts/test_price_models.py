#!/usr/bin/env python3
"""Self-test for price_models.py against a panel with a KNOWN answer.

The real panel needs BigQuery and costs about $0.55 to build, so the estimator
cannot be checked by staring at its output on real data - there is nothing to
check it against. This generates a synthetic panel where the true elasticity,
the true distribution coefficient and the amount of mix contamination are all
chosen by us, then asserts the estimator recovers them.

Two things it proves, which are the two claims price_models.py makes:

  1. The CONTROLLED specification recovers the planted elasticity while the raw
     and within-only ones do not. That is the whole argument for reporting three
     numbers instead of one, and this test found the point the hard way: with
     distribution growing over the window and correlated with price, within-
     cluster alone lands at about -1.73 against a planted -1.50. Cluster fixed
     effects are not sufficient; the distribution control is what closes it.

  2. The unit-value / fixed-weight divergence diagnostic actually fires when mix
     is moving. It is easy to write a diagnostic that never triggers; this
     builds a panel where mix moves lumpily and asserts the correlation drops.

Deterministic - a fixed LCG, no random seed from the clock - so a failure here
is a real regression and not a bad draw.

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

TRUE_ELASTICITY = -1.50
TRUE_STORES = 0.35
TOLERANCE = 0.15          # the estimator must land within this of the planted value


def lcg(seed):
    state = [seed]

    def rnd():
        state[0] = (1103515245 * state[0] + 12345) % (2 ** 31)
        return state[0] / 2 ** 31
    return rnd


def make_panel(path, lumpy_mix, seed=777):
    """Panel with a known elasticity. `lumpy_mix` controls whether the
    unit-value series diverges from the fixed-weight one."""
    rnd = lcg(seed)
    months = [f"{y}-{m:02d}" for y in range(2019, 2026) for m in range(1, 13)]
    rows = []
    families = ["Original", "Berry", "Citrus", "Tropical",
                "Watermelon", "Sour & candy", "Grape", "Coffee & cream"]
    for ci, cluster in enumerate(families):
        base = 2_000_000 * (1 + ci)
        for t, m in enumerate(months):
            moy = int(m[5:7])
            season = 0.12 * math.sin(2 * math.pi * (moy - 3) / 12)
            promo = 1 if rnd() < 0.18 else 0
            idx = math.exp(0.02 * math.sin(t / 7.0) + 0.01 * (rnd() - 0.5) - 0.06 * promo)
            stores = 30000 + 60 * t
            lq = (math.log(base)
                  + TRUE_ELASTICITY * math.log(idx)
                  + season
                  + TRUE_STORES * math.log(stores / 30000)
                  + 0.03 * (rnd() - 0.5))
            units = math.exp(lq)
            # Mix contamination lives ONLY in the unit-value series, which is
            # exactly how it behaves in real data: the fixed basket is immune.
            mix = (1 + 0.30 * rnd()) if lumpy_mix else (1 + 0.25 * (t / len(months)))
            rows.append({
                "scheme": "family", "cluster": cluster, "month": m,
                "rev": round(units * idx * 2.9 * mix, 2), "units": round(units),
                "skus": 40, "stores": int(stores),
                "price_unitvalue": round(idx * 2.9 * mix, 4),
                "price_index": round(idx, 5), "matched_share": 0.9,
                "disc_rate": round(0.05 + 0.25 * promo, 4),
                "disc_txn_rate": round(0.05 + 0.20 * promo, 4),
            })
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def run(path):
    out = subprocess.run(
        [sys.executable, os.path.join(HERE, "price_models.py"), "--panel", path],
        capture_output=True, text=True, timeout=600)
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
        # --- case 1: smooth mix. Estimator must recover the planted values. ---
        p1 = os.path.join(tmp, "smooth.csv")
        n = make_panel(p1, lumpy_mix=False)
        t1 = run(p1)
        within = grab(t1, "within cluster")
        ctrl = grab(t1, "within + distribution + season")
        stores = grab(t1, "distribution coefficient")
        raw = grab(t1, "raw pooled")
        print(f"panel: {n} cluster-months, planted elasticity {TRUE_ELASTICITY}, "
              f"distribution {TRUE_STORES}")
        print(f"  raw pooled        {raw}")
        print(f"  within cluster    {within}   (want {TRUE_ELASTICITY} +/- {TOLERANCE})")
        print(f"  controlled        {ctrl}   (want {TRUE_ELASTICITY} +/- {TOLERANCE})")
        print(f"  distribution      {stores}   (want {TRUE_STORES} +/- {TOLERANCE})")

        # The CONTROLLED specification is the one that must be right. The raw and
        # within-only ones are expected to be biased, and asserting that they are
        # is the point: the synthetic panel has distribution growing over time and
        # correlated with price, so within-cluster alone inherits that bias
        # (~-1.73 against a planted -1.50). If all three agreed, the page would be
        # reporting three numbers for no reason.
        if within is not None and abs(within - TRUE_ELASTICITY) <= abs(ctrl - TRUE_ELASTICITY):
            fails.append("within-only was no worse than the controlled spec — the "
                         "distribution control is doing nothing, which breaks the "
                         "argument for reporting three specifications")
        if ctrl is None or abs(ctrl - TRUE_ELASTICITY) > TOLERANCE:
            fails.append(f"controlled elasticity {ctrl} misses {TRUE_ELASTICITY}")
        if stores is None or abs(stores - TRUE_STORES) > TOLERANCE:
            fails.append(f"distribution coefficient {stores} misses {TRUE_STORES}")
        if raw is None or abs(raw - TRUE_ELASTICITY) <= TOLERANCE:
            fails.append("raw pooled OLS recovered the truth — the panel is not "
                         "exercising the bias this script exists to demonstrate")

        # --- case 2: lumpy mix. The divergence diagnostic must FIRE. ---------
        p2 = os.path.join(tmp, "lumpy.csv")
        make_panel(p2, lumpy_mix=True)
        t2 = run(p2)
        fired = "mix is doing the moving" in t2
        r = grab(t2, "unit-value vs fixed-weight")
        print(f"\nlumpy-mix panel: unit-value vs fixed-weight r = {r}, "
              f"warning fired = {fired}")
        if not fired:
            fails.append("mix-divergence warning did not fire on a lumpy-mix panel")
        # And the elasticity must survive the contamination, because the model
        # never touches the unit-value series.
        ctrl2 = grab(t2, "within + distribution + season")
        print(f"  controlled elasticity under contamination {ctrl2} "
              f"(want {TRUE_ELASTICITY} +/- {TOLERANCE})")
        if ctrl2 is None or abs(ctrl2 - TRUE_ELASTICITY) > TOLERANCE:
            fails.append(f"contaminated-panel elasticity {ctrl2} misses {TRUE_ELASTICITY}")

    if fails:
        print("\nFAILED:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("\nall assertions passed")


if __name__ == "__main__":
    main()
