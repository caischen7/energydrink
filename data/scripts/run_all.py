#!/usr/bin/env python3
"""run_all.py — run every energy-drink scraper with one command.

Instead of running scrape_amazon.py, scrape_walmart.py, ... one by one, this
drives them all in a sensible order, passes through the common options, keeps
going if one fails, and prints a summary at the end. Each scraper still writes
its own CSVs and merges incrementally, exactly as if you'd run it directly.

Order (safest / most-automated first, most bot-fragile last):
  1. youtube   (official API or yt-dlp — no browser, no bot wall)
  2. reddit    (public JSON — no browser, no bot wall)
  3. amazon    (browser)
  4. walmart   (browser)
  5. retailers (browser; Kroger via its free API)
  6. instagram (instaloader)
  7. tiktok    (browser)
  8. facebook  (browser — Meta Ad Library)

Usage (VS Code terminal on macOS):
  pip3 install playwright && python3 -m playwright install chromium   # once
  python3 data/scripts/run_all.py                 # run everything
  python3 data/scripts/run_all.py --only youtube reddit amazon
  python3 data/scripts/run_all.py --skip facebook tiktok
  python3 data/scripts/run_all.py --headless      # hands-off (see note below)
  python3 data/scripts/run_all.py --light         # small, fast test run
  python3 data/scripts/run_all.py --build         # also rebuild dashboard.json
  python3 data/scripts/run_all.py --dry-run       # print the plan, run nothing

HANDS-OFF / bot tests — read this:
  The browser scrapers use a PERSISTENT Chromium profile, so any "press &
  hold" / captcha you solve is remembered. The one-time workflow is:
    1) First run WITHOUT --headless. Solve a challenge in the window if one
       appears (usually only Walmart/Amazon, once each). The cookie is saved.
    2) Every run after that: add --headless — the saved profiles sail through
       and nothing needs clicking.
  There is no honest way to guarantee zero manual solves on the very first
  visit (the challenge scores real pointer motion), but after that first pass
  it is effectively hands-off. YouTube + Reddit never challenge at all.
"""

import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

# Each scraper: the flags it accepts (so we only pass what it understands),
# which "group" it belongs to (drives ordering + preflight), and any env keys
# that unlock/upgrade it.
SCRAPERS = [
    {"name": "youtube", "group": "api",
     "supports": {"sleep"},
     "env": ["YOUTUBE_API_KEY"],
     "note": "official API if YOUTUBE_API_KEY set, else yt-dlp (pip3 install yt-dlp)"},
    {"name": "reddit", "group": "api",
     "supports": {"sleep"},
     "env": [],
     "note": "public JSON (stdlib); optional free praw app via REDDIT_* env"},
    {"name": "amazon", "group": "browser",
     "supports": {"headless", "sleep", "terms"},
     "env": [],
     "note": "browser; solve the text CAPTCHA once (profile remembers)"},
    {"name": "walmart", "group": "browser",
     "supports": {"headless", "sleep", "terms", "fresh"},
     "env": ["SERPAPI_KEY"],
     "note": "browser; auto press-and-hold, else solve once"},
    {"name": "retailers", "group": "browser",
     "supports": {"headless", "sleep", "terms", "fresh"},
     # Kroger has its own dedicated scraper below, so exclude it here to
     # avoid scraping it twice.
     "fixed": ["--retailers", "target", "traderjoes", "publix", "heb",
               "costco", "wholefoods"],
     "env": [],
     "note": "Target/TJ's/Publix/H-E-B/Costco/Whole Foods (browser)"},
    {"name": "kroger", "group": "browser",
     "supports": {"headless", "sleep", "terms", "fresh"},
     "env": ["KROGER_CLIENT_ID", "KROGER_CLIENT_SECRET"],
     "note": "Kroger — official free API if KROGER_* set, else kroger.com direct"},
    {"name": "instagram", "group": "instaloader",
     "supports": {"sleep"},
     "env": [],
     "note": "instaloader (pip3 install instaloader); slow, polite"},
    {"name": "tiktok", "group": "browser",
     "supports": {"headless", "sleep", "fresh"},
     "env": [],
     "note": "browser; solve the puzzle once (profile remembers)"},
    {"name": "facebook", "group": "browser",
     "supports": {"headless", "sleep", "fresh"},
     "env": [],
     "note": "Meta Ad Library (public, usually no challenge)"},
]

# Per-scraper "light mode" caps for a quick smoke run.
LIGHT_FLAGS = {
    "youtube": ["--max-videos-per-query", "10", "--comment-pages", "1"],
    "reddit": ["--max-posts", "80", "--max-comments-per-post", "50"],
    "amazon": ["--max-products", "5", "--search-pages", "1"],
    "walmart": ["--max-products", "5", "--search-pages", "1", "--review-pages", "1"],
    "retailers": ["--max-products", "5", "--review-products", "3"],
    "kroger": ["--max-products", "5", "--review-products", "3"],
    "instagram": ["--max-posts", "15"],
    "tiktok": ["--scrolls", "2"],
    "facebook": ["--scrolls", "2"],
}

# Per-scraper "deep mode" — gather as much market data as reasonable in one
# pass (more products, more review pages, more scroll depth). Slower and a bit
# more bot-exposed, so pair it with generous --sleep and, after the first
# solve, --headless.
DEEP_FLAGS = {
    "youtube": ["--max-videos-per-query", "50", "--comment-pages", "5"],
    "reddit": ["--max-posts", "1000", "--max-comments-per-post", "500"],
    "amazon": ["--max-products", "40", "--search-pages", "3"],
    "walmart": ["--max-products", "40", "--search-pages", "3", "--review-pages", "6"],
    "retailers": ["--max-products", "40", "--review-products", "15", "--scrolls", "6"],
    "kroger": ["--max-products", "40", "--review-products", "15", "--scrolls", "6"],
    "instagram": ["--max-posts", "200"],
    "tiktok": ["--scrolls", "12", "--comments", "5"],
    "facebook": ["--scrolls", "12"],
}

BY_NAME = {s["name"]: s for s in SCRAPERS}


def build_command(scraper, args):
    """Return the argv list for one scraper given the runner's options."""
    cmd = [sys.executable, os.path.join(HERE, "scrape_%s.py" % scraper["name"])]
    cmd += scraper.get("fixed", [])
    sup = scraper["supports"]
    if args.headless and "headless" in sup:
        cmd.append("--headless")
    if args.fresh and "fresh" in sup:
        cmd.append("--fresh")
    if args.sleep is not None and "sleep" in sup:
        cmd += ["--sleep", str(args.sleep)]
    if args.terms and "terms" in sup:
        cmd += ["--terms"] + args.terms
    if getattr(args, "light", False):
        cmd += LIGHT_FLAGS.get(scraper["name"], [])
    elif getattr(args, "deep", False):
        cmd += DEEP_FLAGS.get(scraper["name"], [])
    return cmd


def classify(returncode, tail):
    if returncode == 0:
        return "OK"
    if any("BLOCKED" in line for line in tail):
        return "BLOCKED"
    return "FAILED"


def stream_run(cmd):
    """Run cmd, echo its output live, and keep the last lines for classifying.
    Returns (returncode, tail_lines)."""
    tail = []
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, cwd=REPO, text=True,
                            bufsize=1)
    try:
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            tail.append(line.rstrip("\n"))
            if len(tail) > 25:
                tail.pop(0)
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        raise
    return proc.returncode, tail


def preflight(selected):
    """Warn (don't fail) about missing deps / env keys before running."""
    print("Plan:")
    needs_browser = any(BY_NAME[n]["group"] == "browser" for n in selected)
    if needs_browser:
        try:
            import playwright  # noqa: F401
        except ImportError:
            print("  ! Playwright not installed — browser scrapers will exit "
                  "with instructions. Fix: pip3 install playwright && "
                  "python3 -m playwright install chromium")
    for name in selected:
        s = BY_NAME[name]
        env_state = ""
        if s["env"]:
            present = [e for e in s["env"] if os.environ.get(e)]
            missing = [e for e in s["env"] if not os.environ.get(e)]
            if present:
                env_state = "  [env: %s set]" % ", ".join(present)
            elif missing:
                env_state = "  [optional env unset: %s]" % ", ".join(missing)
        print("  %-10s %s%s" % (name, s["note"], env_state))
    print()


def main():
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run a single scraper directly (e.g. python3 "
               "data/scripts/scrape_walmart.py --help) for its full options.")
    order = [s["name"] for s in SCRAPERS]
    ap.add_argument("--only", nargs="+", choices=order, metavar="SCRAPER",
                    help="run only these (default: all)")
    ap.add_argument("--skip", nargs="+", choices=order, metavar="SCRAPER",
                    default=[], help="run everything except these")
    ap.add_argument("--headless", action="store_true",
                    help="pass --headless to browser scrapers (only after "
                         "you've solved each site's challenge once)")
    ap.add_argument("--fresh", action="store_true",
                    help="overwrite CSVs instead of merging (where supported)")
    ap.add_argument("--sleep", type=float, default=None,
                    help="override base delay (seconds) for every scraper")
    ap.add_argument("--terms", nargs="+", default=None,
                    help="product search terms for amazon/walmart/retailers")
    volume = ap.add_mutually_exclusive_group()
    volume.add_argument("--light", action="store_true",
                        help="small, fast run for testing the whole pipeline")
    volume.add_argument("--deep", action="store_true",
                        help="gather as much data as reasonable per source "
                             "(more products, review pages, scroll depth)")
    ap.add_argument("--build", action="store_true",
                    help="run build_dashboard_json.py after scraping")
    ap.add_argument("--continue-on-error", dest="cont", action="store_true",
                    default=True, help="keep going if a scraper fails (default)")
    ap.add_argument("--stop-on-error", dest="cont", action="store_false",
                    help="stop at the first failing scraper")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan and the exact commands, run nothing")
    args = ap.parse_args()

    selected = [n for n in order
                if (not args.only or n in args.only) and n not in args.skip]
    if not selected:
        sys.exit("Nothing selected.")

    preflight(selected)

    if args.dry_run:
        for name in selected:
            print("  " + " ".join(build_command(BY_NAME[name], args)))
        return

    if not args.headless and any(BY_NAME[n]["group"] == "browser"
                                 for n in selected):
        print(">> Browser windows will open. If a site shows a challenge, "
              "solve it once — it's saved for next time. Re-run with "
              "--headless afterward for hands-off runs.\n")

    results = []
    for name in selected:
        scraper = BY_NAME[name]
        cmd = build_command(scraper, args)
        print("=" * 70)
        print("RUN  %s" % name)
        print("=" * 70)
        start = time.time()
        try:
            rc, tail = stream_run(cmd)
        except KeyboardInterrupt:
            print("\nInterrupted by user — stopping.")
            results.append((name, "INTERRUPTED", time.time() - start))
            break
        status = classify(rc, tail)
        results.append((name, status, time.time() - start))
        print("\n-> %s: %s (%.0fs)\n" % (name, status, time.time() - start))
        if status != "OK" and not args.cont:
            print("Stopping (--stop-on-error).")
            break

    if args.build and any(s == "OK" for _, s, _ in results):
        print("=" * 70)
        print("RUN  build_dashboard_json.py")
        print("=" * 70)
        stream_run([sys.executable,
                    os.path.join(HERE, "build_dashboard_json.py")])

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for name, status, secs in results:
        print("  %-10s %-11s %5.0fs" % (name, status, secs))
    blocked = [n for n, s, _ in results if s == "BLOCKED"]
    failed = [n for n, s, _ in results if s == "FAILED"]
    if blocked:
        print("\nBlocked (bot wall / rate limit): %s" % ", ".join(blocked))
        print("  -> rerun those WITHOUT --headless and solve the challenge "
              "once, or wait and retry later.")
    if failed:
        print("\nFailed: %s  (scroll up for each one's error)" % ", ".join(failed))
    ok = sum(1 for _, s, _ in results if s == "OK")
    print("\n%d/%d scrapers OK." % (ok, len(results)))
    if failed or blocked:
        sys.exit(1)


if __name__ == "__main__":
    main()
