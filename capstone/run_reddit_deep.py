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


def setup_env():
    """Write a .env beside this script, interactively.

    WHY INTERACTIVE RATHER THAN A TEMPLATE TO EDIT
    A pasted `export REDDIT_CLIENT_SECRET=...` lands in shell history in
    plaintext, and a filled-in template tends to get mailed, uploaded or
    committed. Reading the secret with getpass keeps it off the screen and out
    of history, and the file is written 0600 so it is readable only by you.

    The secret is never echoed, never logged, and never leaves this machine.
    """
    import getpass
    import stat

    path = os.path.join(HERE, ".env")
    if os.path.exists(path):
        print(f"\n  {path} already exists.")
        if input("  Overwrite it? [y/N] ").strip().lower() not in ("y", "yes"):
            print("  Left alone.")
            return 0

    print(f"""
  Creating {path}

  Get these from your app at https://www.reddit.com/prefs/apps
    Client ID     — shown under the app name (or in the Edit App panel)
    Client secret — the 'secret' field; typing it here will NOT be shown

  If you have ever pasted the secret into a chat, an email or a screenshot,
  regenerate it on that page FIRST and use the new one here.
""")
    cid = input("  Client ID: ").strip()
    sec = getpass.getpass("  Client secret (hidden): ").strip()
    user = input("  Your Reddit username (no /u/): ").strip().lstrip("/").removeprefix("u/")

    if not (cid and sec and user):
        print("\n  All three are required. Nothing written.")
        return 1
    if len(sec) < 10:
        print("\n  That secret looks too short — check you copied the whole "
              "'secret' field and not the Client ID. Nothing written.")
        return 1

    ua = f"script:energydrink-capstone:v1 (by /u/{user})"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# Reddit Data API credentials. Local only — never commit, "
                 "upload or paste these.\n"
                 "# Regenerate the secret at https://www.reddit.com/prefs/apps "
                 "if it is ever exposed.\n")
        fh.write(f"REDDIT_CLIENT_ID={cid}\n")
        fh.write(f"REDDIT_CLIENT_SECRET={sec}\n")
        fh.write(f"REDDIT_USER_AGENT={ua}\n")
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)        # 0600, owner only

    print(f"""
  Written, permissions 0600 (only your user can read it).
    user agent: {ua}

  Verify, then do a small first run:
    python3 {sys.argv[0]} --self-test
    python3 {sys.argv[0]} --max-posts 500
""")
    return 0


def preflight():
    """Fail with something actionable rather than a traceback."""
    missing = [k for k in ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET",
                           "REDDIT_USER_AGENT") if not os.environ.get(k)]
    if not missing:
        return True
    me = sys.argv[0] or os.path.abspath(__file__)
    print("\n  Missing credentials:", ", ".join(missing))
    env_path = os.path.join(HERE, ".env")
    tmpl = os.path.join(HERE, ".env.example")
    # The bundled copy has no .env.example beside it, so offer to write one
    # rather than pointing at a file that is not there.
    step1 = (f"1. Fill in the template:\n       {tmpl}\n       -> save as {env_path}"
             if os.path.exists(tmpl) else
             f"1. Run this and follow the prompts (easiest):\n"
             f"       python3 {sys.argv[0]} --setup\n\n"
             f"   Or create {env_path} by hand with these three lines:\n"
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
       python3 {me} --self-test
       python3 {me} --dry-run
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

    # -- 3. credentials are read at CALL time, not import time --------------
    # Regression guard. reddit_collector had `UA = os.environ.get(...)` at
    # module level; the bundle installs modules before main() loads the .env,
    # so UA was frozen as "" and a real run died with "Missing credentials"
    # immediately after reporting it had loaded three variables. Any env read
    # that happens at import time reintroduces this, so the test sets the
    # variables AFTER the import and asserts the collector still sees them.
    try:
        import reddit_collector as rc2
        saved = {k: os.environ.get(k) for k in
                 ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT")}
        try:
            os.environ["REDDIT_CLIENT_ID"] = "probe_id"
            os.environ["REDDIT_CLIENT_SECRET"] = "probe_secret_value"
            os.environ["REDDIT_USER_AGENT"] = "script:probe:v1 (by /u/probe)"
            assert rc2.ua() == "script:probe:v1 (by /u/probe)", (
                f"user agent read at import time, not call time: {rc2.ua()!r}")
            # token() must get past its own credential check and fail only on
            # the network call, which is what SystemExit here would rule out.
            try:
                rc2.token()
            except SystemExit as e:
                raise AssertionError(
                    f"credential check rejected env vars set after import: {e}")
            except Exception:
                pass          # network failure is expected and fine
            ok.append("credentials: read at call time, survive a late .env load")
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    except AssertionError as e:
        fail.append(f"credentials: {e}")
    except Exception as e:
        fail.append(f"credentials: {type(e).__name__}: {e}")

    # -- 4. writer ----------------------------------------------------------
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
    ap.add_argument("--setup", action="store_true",
                    help="create the .env credentials file interactively "
                         "(secret is typed hidden, never echoed or logged)")
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

    env_file = os.path.join(HERE, ".env")
    n = load_dotenv(env_file)
    if n:
        # The real path, not a hardcoded repo-relative one. The bundled copy
        # lives wherever the user put it, and printing "capstone/.env" to
        # someone whose file is on their Desktop is just confusing.
        print(f"  loaded {n} variable(s) from {env_file}")

    if a.setup:
        sys.exit(setup_env())
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
