#!/usr/bin/env python3
"""One entry point for the *additional* data sources.

Runs the live scrapers in `data/scrapers/` (Open Food Facts, Wikipedia) against
the network, or — with `--sample` — generates same-schema placeholder data so
everything downstream still has something to read when the network isn't
available (locked-down sandbox, offline CI, fresh checkout).

    python data/scripts/run_scrapers.py                 # live scrape all new sources
    python data/scripts/run_scrapers.py --source off    # just Open Food Facts
    python data/scripts/run_scrapers.py --sample        # generate samples into data/
    python data/scripts/run_scrapers.py --sample --out data/sample

After it finishes, refresh the dashboard aggregate:
    python data/scripts/build_dashboard_json.py
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRAPERS = os.path.join(os.path.dirname(HERE), "scrapers")

LIVE = {
    "off": ("Open Food Facts", os.path.join(SCRAPERS, "openfoodfacts.py")),
    "wiki": ("Wikipedia pageviews", os.path.join(SCRAPERS, "wikipedia.py")),
}
# maps the --source keys onto generate_sample_data.py source names
SAMPLE_NAME = {"off": "openfoodfacts", "wiki": "wikipedia"}


def run_live(keys):
    ok = True
    for k in keys:
        label, script = LIVE[k]
        print(f"\n=== {label} (live) ===")
        rc = subprocess.call([sys.executable, script])
        if rc != 0:
            print(f"  ! {label} exited {rc}", file=sys.stderr)
            ok = False
    return ok


def run_sample(keys, out):
    only = ",".join(SAMPLE_NAME[k] for k in keys)
    print(f"\n=== generating sample data for: {only} -> {out} ===")
    return subprocess.call([
        sys.executable, os.path.join(HERE, "generate_sample_data.py"),
        "--only", only, "--out", out,
    ]) == 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=list(LIVE) + ["all"], default="all")
    ap.add_argument("--sample", action="store_true",
                    help="generate placeholder data instead of scraping the network")
    ap.add_argument("--out", default="data",
                    help="output dir for --sample (default: data)")
    args = ap.parse_args()

    keys = list(LIVE) if args.source == "all" else [args.source]
    ok = run_sample(keys, args.out) if args.sample else run_live(keys)

    if ok:
        print("\nDone. Now run: python data/scripts/build_dashboard_json.py")
    else:
        print("\nFinished with errors (see above).", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
