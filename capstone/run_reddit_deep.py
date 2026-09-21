#!/usr/bin/env python3
"""RUN THIS ONE. Deep Reddit pull for r/EnergyDrinks — open in VS Code and hit Run.

    python capstone/run_reddit_deep.py --self-test   # no credentials, no network
    python capstone/run_reddit_deep.py --dry-run     # show the plan, call nothing
    python capstone/run_reddit_deep.py               # real pull, bounded (see below)

WHY THIS FILE EXISTS
--------------------
capstone/collectors/reddit_collector.py is the implementation and takes a dozen
flags. This is the front door: deep mode on by default, a bounded first run so
nobody accidentally starts a 14-hour job, credentials loaded from a .env file
the way VS Code users expect, and a self-test that proves the whole chain works
before you spend any quota.

It deliberately does NOT re-implement the flavor rules. CLAUDE.md records what
happened the last time those were hand-copied into a second file: the copy got
cherry and mango wrong and silently disagreed with every other page in the
project. One definition, imported.

CREDENTIALS
-----------
Create a **script** app at https://www.reddit.com/prefs/apps, then either export
the three variables, or — easier in VS Code — copy capstone/.env.example to
capstone/.env and fill it in. .env is gitignored; it will not be committed.

BEFORE THE FIRST REAL RUN
-------------------------
Read capstone/REDDIT_API_TERMS.md. The project brief makes a current terms
summary a precondition, and deep mode issues a lot more requests than the
original plan did, which makes the free-tier request-cap question load-bearing.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Import the real implementation. Both paths are needed: `collectors` for the
# collector itself, `data/scripts` because the extractor rolls flavors up using
# the same classifier the PDI side uses.
sys.path.insert(0, os.path.join(HERE, "collectors"))
sys.path.insert(0, os.path.join(ROOT, "data", "scripts"))


def load_dotenv(path):
    """Minimal .env reader — no dependency, because asking someone to pip
    install python-dotenv before they can run one script is a bad trade.
    Ignores blanks and comments, strips optional quotes, and never overwrites a
    variable that is already set in the real environment."""
    if not os.path.exists(path):
        return 0
    n = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and not os.environ.get(k):
                os.environ[k] = v
                n += 1
    return n


def preflight():
    """Fail with something actionable rather than a traceback."""
    missing = [k for k in ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET",
                           "REDDIT_USER_AGENT") if not os.environ.get(k)]
    if not missing:
        return True
    print("\n  Missing credentials:", ", ".join(missing))
    env_path = os.path.join(HERE, ".env")
    tmpl = os.path.join(HERE, ".env.example")
    # The bundled copy has no .env.example beside it, so offer to write one
    # rather than pointing at a file that is not there.
    step1 = (f"1. Fill in the template:\n       {tmpl}\n       -> save as {env_path}"
             if os.path.exists(tmpl) else
             f"1. Create {env_path} with these three lines:\n"
             f"       REDDIT_CLIENT_ID=...\n"
             f"       REDDIT_CLIENT_SECRET=...\n"
             f'       REDDIT_USER_AGENT=script:bogus-banana-capstone:v1 (by /u/<you>)')
    print(f"""
  Two ways to fix it:

  {step1}

  2. Or export them in your shell:
       export REDDIT_CLIENT_ID=...
       export REDDIT_CLIENT_SECRET=...
       export REDDIT_USER_AGENT="script:bogus-banana-capstone:v1 (by /u/<you>)"

  Get the values by creating a **script** app at
  https://www.reddit.com/prefs/apps  (the client id is the string under the app
  name; the secret is the field labelled "secret").

  No credentials needed to try these first:
       python capstone/run_reddit_deep.py --self-test
       python capstone/run_reddit_deep.py --dry-run
""")
    return False


def self_test():
    """Prove the whole chain works before spending any quota or credentials.

    Runs three things:
      1. the extractor against real committed text (so you see actual output),
      2. the partitioning logic against a mock Reddit that enforces the real
         1,000-item listing cap,
      3. the CSV writer, into a temp dir.

    No network. No credentials. If this passes, the only thing standing between
    you and a real pull is the three environment variables.
    """
    import tempfile
    import csv as _csv
    ok, fail = [], []

    # -- 1. extractor on real text ------------------------------------------
    try:
        from flavor_mentions import extract, analyse
        f, b, _ = extract("The bang mocha was the greatest flavor out! "
                          "Way better than the watermelon one.")
        assert "Coffee" in f, f"expected Coffee in {f}"
        assert "Watermelon" in f, f"expected Watermelon in {f}"
        assert "Bang" in b, f"expected Bang in {b}"
        ok.append(f"extractor: flavors={sorted(f)} brands={sorted(b)}")

        # the context gate must still reject a bare competing-beverage mention
        f2, _, _ = extract("I only have 1 cup of coffee in the morning")
        assert "Coffee" not in f2, f"context gate leaked: {f2}"
        ok.append("context gate: 'cup of coffee in the morning' correctly NOT a flavor")

        corpus = os.path.join(ROOT, "data/youtube/comments.csv")
        if os.path.exists(corpus):
            _csv.field_size_limit(10 ** 7)
            with open(corpus, encoding="utf-8", errors="replace") as fh:
                res = analyse(_csv.DictReader(fh), limit=5000)
            top = ", ".join(f"{r['name']}({r['mentions']})" for r in res["flavors"][:5])
            ok.append(f"real corpus: {res['rows_matched']:,}/{res['rows_seen']:,} matched "
                      f"({res['match_rate_pct']}%) · top: {top}")
        else:
            ok.append("real corpus: skipped (data/youtube/comments.csv not present)")
    except Exception as e:
        fail.append(f"extractor: {type(e).__name__}: {e}")

    # -- 2. partitioning beats the 1,000 cap --------------------------------
    try:
        import reddit_collector as rc
        cap = rc.LISTING_CAP
        TOTAL = 25_000

        def fake_get(path, tok, quota, **p):
            quota.calls += 1
            if "/comments/" in path:
                pid = path.rsplit("/", 1)[-1]
                return [{}, {"data": {"children": [
                    {"kind": "t1", "data": {"body": f"c{i} {pid} mango flavor"}}
                    for i in range(5)]}}]
            seed = hash((p.get("q"), p.get("sort"), p.get("t"))) % TOTAL
            off = int(p.get("after") or 0)
            if off >= cap:
                return {"data": {"children": [], "after": None}}
            kids = [{"data": {"id": f"p{(seed+off+i) % TOTAL}",
                              "created_utc": 1_700_000_000 + i,
                              "title": "watermelon flavor post", "selftext": ""}}
                    for i in range(rc.PAGE)]
            nxt = off + rc.PAGE
            return {"data": {"children": kids,
                             "after": str(nxt) if nxt < cap else None}}

        real_get, real_sleep, real_subs = rc.get, rc.SLEEP, rc.SUBREDDITS
        rc.get, rc.SLEEP, rc.SUBREDDITS = fake_get, 0, ["EnergyDrinks"]
        q = rc.Quota()
        rc.SEARCH_TERMS = ["flavor"]
        list(rc.harvest("mock", q, months=600, verbose=False, deep=False))
        std = rc.harvest.stats["posts_unique"]
        rc.DEEP_TERMS = ["the", "it", "a", "flavor", "best", "worst"]
        rc.DEEP_SORTS, rc.DEEP_WINDOWS = ["new", "top", "relevance"], ["all", "year"]
        texts = list(rc.harvest("mock", q, months=600, verbose=False, deep=True))
        deep = rc.harvest.stats
        rc.get, rc.SLEEP, rc.SUBREDDITS = real_get, real_sleep, real_subs

        assert std <= cap, f"standard mode returned {std}, above the cap — mock is wrong"
        assert deep["posts_unique"] > cap, (
            f"deep mode got {deep['posts_unique']:,}, did NOT beat the {cap:,} cap")
        ok.append(f"standard mode: {std:,} unique posts (capped at {cap:,}, as expected)")
        ok.append(f"deep mode:     {deep['posts_unique']:,} unique posts "
                  f"— {deep['posts_unique']/cap:.0f}x past the cap")
        ok.append(f"dedupe:        {deep['posts_raw']:,} raw hits -> "
                  f"{deep['posts_raw']-deep['posts_unique']:,} duplicates removed")
        ok.append(f"comment walk:  {deep['comments']:,} comments, {len(texts):,} texts total")
    except Exception as e:
        fail.append(f"partitioning: {type(e).__name__}: {e}")

    # -- 3. writer ----------------------------------------------------------
    try:
        import reddit_collector as rc
        with tempfile.TemporaryDirectory() as tmp:
            real_out = rc.OUT_DIR
            rc.OUT_DIR = tmp
            rc.write({"flavors": [{"name": "Mango", "mentions": 3}],
                      "brands": [{"name": "Bang", "mentions": 2}],
                      "rows_seen": 3, "rows_matched": 3, "match_rate_pct": 100.0,
                      "engine": "test", "quota": {"calls": 1}}, months=24)
            rc.OUT_DIR = real_out
            assert len(os.listdir(tmp)) == 3, os.listdir(tmp)
        ok.append("writer: 3 CSVs written and verified")
    except Exception as e:
        fail.append(f"writer: {type(e).__name__}: {e}")

    print("\n  SELF-TEST — no network, no credentials\n")
    for line in ok:
        print(f"    ok   {line}")
    for line in fail:
        print(f"    FAIL {line}")
    if fail:
        print(f"\n  {len(fail)} FAILED\n")
        return 1
    creds = all(os.environ.get(k) for k in
                ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT"))
    print(f"\n  ALL PASSED — the pipeline works end to end.")
    print(f"  Credentials: {'found, you can do a real run' if creds else 'NOT set — see --help'}\n")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="Deep Reddit pull for the flavor study.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)
    ap.add_argument("--self-test", action="store_true",
                    help="verify the whole chain offline, then exit")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan without making a single call")
    ap.add_argument("--max-posts", type=int, default=2000,
                    help="stop after N UNIQUE posts. Default 2000 (~35-45 min) so a "
                         "first run is bounded; raise it once you have seen the output. "
                         "0 means no limit and is a multi-hour job.")
    ap.add_argument("--months", type=int, default=36,
                    help="how far back to keep posts (default 36)")
    ap.add_argument("--standard", action="store_true",
                    help="use the narrow non-partitioned plan instead of deep mode")
    a = ap.parse_args()

    n = load_dotenv(os.path.join(HERE, ".env"))
    if n:
        print(f"  loaded {n} variable(s) from capstone/.env")

    if a.self_test:
        sys.exit(self_test())

    import reddit_collector as rc
    deep = not a.standard

    if a.dry_run:
        rc.plan(deep)
        return
    if not preflight():
        sys.exit(1)

    print(f"\n  Deep pull starting. Ctrl-C is safe — responses are cached, so a "
          f"restart resumes.\n  Bound: {a.max_posts or 'NONE (multi-hour)'} unique posts, "
          f"{a.months} months back.\n")
    res = rc.run(a.months, limit=None, verbose=True, deep=deep,
                 max_posts=a.max_posts or None)
    h = res.get("harvest", {})
    print(f"\n  {res['rows_seen']:,} texts · {res['rows_matched']:,} matched "
          f"({res['match_rate_pct']}%) · {res['quota']['calls']} API calls")
    if h:
        print(f"  {h['queries']} partitions · {h['posts_raw']:,} hits -> "
              f"{h['posts_unique']:,} UNIQUE posts "
              f"({h['posts_raw']-h['posts_unique']:,} dupes) · {h['comments']:,} comments")
        if h["posts_unique"] > rc.LISTING_CAP:
            print(f"  -> cleared the {rc.LISTING_CAP:,}-item listing cap")
    rc.write(res, a.months)
    print("\n  Top flavors:")
    for r in res["flavors"][:10]:
        print(f"    {r['name']:<16}{r['mentions']:>7,}  {r['mention_share_pct']:>6}% "
              f" net {r['net_sentiment']:>6}")
    print()


if __name__ == "__main__":
    main()
