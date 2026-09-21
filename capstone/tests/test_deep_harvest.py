#!/usr/bin/env python3
"""Prove the partitioning actually clears the 1,000-item listing cap.

    python capstone/tests/test_deep_harvest.py

Runs harvest() against a MOCK Reddit that enforces the real constraints:
  - any single listing serves at most LISTING_CAP items, then stops
  - pages are PAGE items with an `after` cursor
  - different (term, sort, window) partitions return overlapping but
    different slices of one underlying subreddit

No network. The point is the union math: if partitioning works, unique posts
must exceed what any one listing could ever return.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "capstone/collectors"))
import reddit_collector as rc  # noqa: E402

# A synthetic subreddit far larger than one listing can serve.
TOTAL_POSTS = 25_000
COMMENTS_PER_POST = 8


def make_mock():
    """Each partition sees a deterministic, overlapping slice of the corpus."""
    calls = {"n": 0}

    def fake_get(path, tok, quota, **p):
        calls["n"] += 1
        quota.calls += 1
        if "/comments/" in path:
            pid = path.rsplit("/", 1)[-1]
            return [{}, {"data": {"children": [
                {"kind": "t1", "data": {"body": f"comment {i} on {pid} mango flavor"}}
                for i in range(COMMENTS_PER_POST)]}}]

        # Deterministic slice per partition, so different partitions overlap
        # heavily without being identical - the real behaviour.
        seed = hash((p.get("q"), p.get("sort"), p.get("t"))) % TOTAL_POSTS
        after = p.get("after")
        offset = int(after) if after else 0
        if offset >= rc.LISTING_CAP:          # the cap: listing is exhausted
            return {"data": {"children": [], "after": None}}
        kids = []
        for i in range(rc.PAGE):
            idx = (seed + offset + i) % TOTAL_POSTS
            kids.append({"data": {
                "id": f"p{idx}",
                "created_utc": 1_700_000_000 + idx,
                "title": f"post {idx} watermelon flavor",
                "selftext": "",
            }})
        nxt = offset + rc.PAGE
        return {"data": {"children": kids,
                         "after": str(nxt) if nxt < rc.LISTING_CAP else None}}

    return fake_get, calls


def main():
    rc.get = make_mock()[0]
    rc.SLEEP = 0
    rc.token = lambda: "mock"
    rc.SUBREDDITS = ["EnergyDrinks"]          # one subreddit, as asked
    quota = rc.Quota()

    fails = []

    # --- standard mode: one term list, one sort, one window ------------------
    rc.SEARCH_TERMS = ["flavor"]
    texts = list(rc.harvest("mock", quota, months=600, verbose=False, deep=False))
    std = rc.harvest.stats
    print(f"standard : {std['queries']:>5} partitions -> "
          f"{std['posts_unique']:>6,} unique posts, {len(texts):>7,} texts")
    if std["posts_unique"] > rc.LISTING_CAP:
        fails.append("standard mode should be capped near LISTING_CAP")

    # --- deep mode: partitioned ---------------------------------------------
    rc.DEEP_TERMS = ["the", "it", "a", "flavor", "taste", "best", "worst", "new"]
    rc.DEEP_SORTS = ["new", "top", "relevance"]
    rc.DEEP_WINDOWS = ["all", "year"]
    texts = list(rc.harvest("mock", quota, months=600, verbose=False, deep=True))
    deep = rc.harvest.stats
    print(f"deep     : {deep['queries']:>5} partitions -> "
          f"{deep['posts_unique']:>6,} unique posts, {len(texts):>7,} texts")
    print(f"           {deep['posts_raw']:,} raw hits, "
          f"{deep['posts_raw'] - deep['posts_unique']:,} deduplicated")

    # The claim being tested.
    if deep["posts_unique"] <= rc.LISTING_CAP:
        fails.append(f"deep mode returned {deep['posts_unique']:,} unique posts, "
                     f"which does not exceed the {rc.LISTING_CAP:,} cap — "
                     "partitioning is not working")
    if deep["posts_raw"] <= deep["posts_unique"]:
        fails.append("no duplicates across partitions — the mock is not "
                     "overlapping, so the dedupe path is untested")
    # Texts must include comments, not just post bodies.
    if deep["comments"] < deep["posts_unique"]:
        fails.append("comment trees are not being walked")

    print()
    if fails:
        for f in fails:
            print("  FAIL:", f)
        sys.exit(1)
    print(f"  PASS — deep mode cleared the {rc.LISTING_CAP:,}-item cap "
          f"({deep['posts_unique']:,} unique), dedupe and comment walk both exercised")


if __name__ == "__main__":
    main()
