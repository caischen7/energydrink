import os
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
#!/usr/bin/env python3
"""Fixture tests for data/scripts/scrape_reddit.py and the build_reddit glob
patch in data/scripts/build_external_datasets.py. No network access —
everything runs against in-memory JSON fixtures and temp dirs."""

import csv
import io
import os
import shutil
import sys
import tempfile
import unittest
import urllib.parse

SCRIPTS = REPO + "/data/scripts"
sys.path.insert(0, SCRIPTS)

import scrape_reddit as sr  # noqa: E402
import build_external_datasets as bed  # noqa: E402


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

def t3(pid, title, selftext="", created=1717000000.0, score=10,
       num_comments=3):
    """A listing child as Reddit returns it — author included on purpose so
    the tests can prove it is never propagated."""
    return {
        "kind": "t3",
        "data": {
            "id": pid,
            "title": title,
            "selftext": selftext,
            "created_utc": created,
            "score": score,
            "num_comments": num_comments,
            "permalink": "/r/EnergyDrinks/comments/%s/slug/" % pid,
            "author": "some_username",
            "author_fullname": "t2_abc",
            "subreddit": "EnergyDrinks",
        },
    }


def listing(children, after):
    return {"kind": "Listing", "data": {"children": children, "after": after}}


COMMENT_TREE = [
    {
        "kind": "t1",
        "data": {
            "id": "c1",
            "link_id": "t3_p1",
            "body": "Celsius over Monster any day",
            "created_utc": 1717000001.0,
            "score": 5,
            "author": "user_a",
            "replies": {
                "kind": "Listing",
                "data": {
                    "children": [
                        {
                            "kind": "t1",
                            "data": {
                                "id": "c2",
                                "link_id": "t3_p1",
                                "body": "agreed",
                                "created_utc": 1717000002.0,
                                "score": 1,
                                "author": "user_b",
                                "replies": "",  # reddit uses "" for none
                            },
                        },
                        # a 'more' stub nested inside the replies
                        {"kind": "more",
                         "data": {"count": 12, "children": ["c3", "c4"]}},
                    ],
                    "after": None,
                },
            },
        },
    },
    # a top-level 'more' stub
    {"kind": "more", "data": {"count": 50, "children": ["c9"]}},
    {
        "kind": "t1",
        "data": {
            "id": "c5",
            "link_id": "t3_p1",
            "body": "the Red Bull crash is real",
            "created_utc": 1717000003.0,
            "score": 2,
            "author": "user_c",
            "replies": "",
        },
    },
]


# --------------------------------------------------------------------------
# Scraper: parsers / transforms
# --------------------------------------------------------------------------

class TestSchemas(unittest.TestCase):
    def test_headers_match_build_reddit_contract(self):
        self.assertEqual(
            sr.POST_COLUMNS,
            ["id", "title", "selftext", "created_utc", "score",
             "num_comments", "permalink"],
        )
        self.assertEqual(
            sr.COMMENT_COLUMNS,
            ["id", "link_id", "body", "created_utc", "score"],
        )


class TestParseListing(unittest.TestCase):
    def test_listing_to_post_rows(self):
        payload = listing(
            [
                t3("p1", "Best sugar free options?", "no crash please"),
                {"kind": "t5", "data": {"id": "nope"}},  # unexpected kind
                t3("p2", "Ghost review", created=1717000100),
            ],
            after="t3_p2",
        )
        rows, after = sr.parse_listing(payload)
        self.assertEqual(after, "t3_p2")
        self.assertEqual([r["id"] for r in rows], ["p1", "p2"])
        for r in rows:
            self.assertEqual(sorted(r.keys()), sorted(sr.POST_COLUMNS))
            self.assertNotIn("author", r)  # privacy: usernames never stored
        r = rows[0]
        self.assertEqual(r["title"], "Best sugar free options?")
        self.assertEqual(r["selftext"], "no crash please")
        self.assertEqual(r["permalink"], "/r/EnergyDrinks/comments/p1/slug/")
        self.assertEqual(r["score"], 10)
        self.assertEqual(r["num_comments"], 3)
        # created_utc stays a raw unix stamp string: build_reddit does
        # int(float(ts))
        self.assertEqual(int(float(r["created_utc"])), 1717000000)

    def test_empty_and_malformed_payloads(self):
        self.assertEqual(sr.parse_listing(None), ([], None))
        self.assertEqual(sr.parse_listing({}), ([], None))
        self.assertEqual(sr.parse_listing({"data": {}}), ([], None))


class TestFlattenComments(unittest.TestCase):
    def test_nested_tree_flattens_without_usernames(self):
        rows = sr.flatten_comments(COMMENT_TREE, cap=300)
        self.assertEqual([r["id"] for r in rows], ["c1", "c2", "c5"])
        for r in rows:
            self.assertEqual(sorted(r.keys()), sorted(sr.COMMENT_COLUMNS))
            self.assertNotIn("author", r)
        self.assertEqual(rows[0]["link_id"], "t3_p1")
        self.assertEqual(rows[0]["body"], "Celsius over Monster any day")
        self.assertEqual(int(float(rows[1]["created_utc"])), 1717000002)
        self.assertEqual(rows[2]["score"], 2)

    def test_more_stubs_are_skipped(self):
        ids = [r["id"] for r in sr.flatten_comments(COMMENT_TREE, cap=300)]
        self.assertNotIn("c3", ids)
        self.assertNotIn("c4", ids)
        self.assertNotIn("c9", ids)

    def test_cap_is_respected_mid_tree(self):
        rows = sr.flatten_comments(COMMENT_TREE, cap=2)
        self.assertEqual([r["id"] for r in rows], ["c1", "c2"])

    def test_empty_children(self):
        self.assertEqual(sr.flatten_comments([], cap=10), [])
        self.assertEqual(sr.flatten_comments(None, cap=10), [])


class TestPublicPostComments(unittest.TestCase):
    def test_comments_endpoint_payload_shape(self):
        calls = []

        def fake_fetch(url):
            calls.append(url)
            return [listing([t3("p1", "title")], None),
                    listing(COMMENT_TREE, None)]

        rows = sr.public_post_comments("p1", 300, sleep=0,
                                       fetch_json=fake_fetch)
        self.assertEqual([r["id"] for r in rows], ["c1", "c2", "c5"])
        self.assertEqual(len(calls), 1)
        self.assertIn("/comments/p1.json", calls[0])
        self.assertIn("limit=500", calls[0])

    def test_malformed_payload_yields_no_rows(self):
        self.assertEqual(
            sr.public_post_comments("p1", 300, sleep=0,
                                    fetch_json=lambda u: {"error": 500}),
            [],
        )


class TestPagination(unittest.TestCase):
    def _fake_reddit(self, log):
        """Serves a tiny fake reddit: new (2 pages), hot, top?t=year/all."""
        def fetch(url):
            parts = urllib.parse.urlsplit(url)
            qs = urllib.parse.parse_qs(parts.query)
            log.append((parts.path, qs))
            after = (qs.get("after") or [None])[0]
            if parts.path.endswith("/new.json"):
                if after is None:
                    return listing([t3("p1", "one"), t3("p2", "two")],
                                   "t3_p2")
                self._seen_after = after
                return listing([t3("p3", "three")], None)
            if parts.path.endswith("/hot.json"):
                return listing([t3("p2", "two dup"), t3("p4", "four")], None)
            if parts.path.endswith("/top.json"):
                if qs["t"] == ["year"]:
                    return listing([t3("p1", "one dup")], None)
                return listing([], None)
            raise AssertionError("unexpected url " + url)
        return fetch

    def test_after_cursor_dedupe_and_exhaustion(self):
        log = []
        posts = sr.public_listing_posts("EnergyDrinks", 800, sleep=0,
                                        fetch_json=self._fake_reddit(log))
        self.assertEqual([p["id"] for p in posts], ["p1", "p2", "p3", "p4"])
        # page 2 of `new` was requested with the page-1 cursor
        self.assertEqual(self._seen_after, "t3_p2")
        # every listing got hit: new x2, hot, top?t=year, top?t=all
        paths = [p for p, _ in log]
        self.assertEqual(paths.count("/r/EnergyDrinks/new.json"), 2)
        self.assertEqual(paths.count("/r/EnergyDrinks/hot.json"), 1)
        self.assertEqual(paths.count("/r/EnergyDrinks/top.json"), 2)
        t_params = [qs["t"][0] for p, qs in log if p.endswith("/top.json")]
        self.assertEqual(sorted(t_params), ["all", "year"])
        # limit=100 requested each time
        self.assertTrue(all(qs["limit"] == ["100"] for _, qs in log))

    def test_max_posts_stops_early(self):
        log = []
        posts = sr.public_listing_posts("EnergyDrinks", 3, sleep=0,
                                        fetch_json=self._fake_reddit(log))
        self.assertEqual([p["id"] for p in posts], ["p1", "p2", "p3"])
        # hot / top never requested once the budget was hit
        self.assertTrue(all(p.endswith("/new.json") for p, _ in log))


class TestMergeIncremental(unittest.TestCase):
    def test_merge_prefers_fresh_rows_and_keeps_header(self):
        tmp = tempfile.mkdtemp()
        try:
            path = os.path.join(tmp, "energydrinks_posts_20260706.csv")
            old = [
                {"id": "a", "title": "old title", "selftext": "",
                 "created_utc": "1717000000.0", "score": "1",
                 "num_comments": "0", "permalink": "/r/x/a/"},
                {"id": "b", "title": "keep me", "selftext": "",
                 "created_utc": "1717000001.0", "score": "2",
                 "num_comments": "1", "permalink": "/r/x/b/"},
            ]
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=sr.POST_COLUMNS)
                w.writeheader()
                w.writerows(old)

            fresh = [
                {"id": "a", "title": "NEW title", "selftext": "now with text",
                 "created_utc": "1717000000.0", "score": "9",
                 "num_comments": "4", "permalink": "/r/x/a/"},
                {"id": "c", "title": "brand new", "selftext": "",
                 "created_utc": "1717000002.0", "score": "3",
                 "num_comments": "0", "permalink": "/r/x/c/"},
            ]
            sr.write_csv_merged(path, sr.POST_COLUMNS, fresh, "id")

            with open(path, encoding="utf-8", newline="") as f:
                header = f.readline().strip()
                self.assertEqual(
                    header,
                    "id,title,selftext,created_utc,score,num_comments,"
                    "permalink",
                )
                f.seek(0)
                rows = {r["id"]: r for r in csv.DictReader(f)}
            self.assertEqual(sorted(rows), ["a", "b", "c"])
            self.assertEqual(rows["a"]["title"], "NEW title")  # fresh wins
            self.assertEqual(rows["a"]["score"], "9")
            self.assertEqual(rows["b"]["title"], "keep me")  # union kept
        finally:
            shutil.rmtree(tmp)


class TestPrawRows(unittest.TestCase):
    def test_praw_post_row_shape(self):
        class Sub(object):
            id = "p9"
            title = "Reign vs Bang"
            selftext = "which one"
            created_utc = 1717000009.0
            score = 42
            num_comments = 7
            permalink = "/r/EnergyDrinks/comments/p9/slug/"
            author = "SHOULD_NEVER_APPEAR"

        row = sr.praw_post_row(Sub())
        self.assertEqual(sorted(row.keys()), sorted(sr.POST_COLUMNS))
        self.assertNotIn("author", row)
        self.assertEqual(row["id"], "p9")
        self.assertEqual(int(float(row["created_utc"])), 1717000009)


class TestHelpers(unittest.TestCase):
    def test_to_int_float_ts(self):
        self.assertEqual(sr.to_int("3"), 3)
        self.assertEqual(sr.to_int(0), 0)
        self.assertIsNone(sr.to_int(None))
        self.assertIsNone(sr.to_int(""))
        self.assertEqual(sr.to_float("1,234.5"), 1234.5)
        self.assertEqual(sr.fmt_ts(1717000000.0), "1717000000.0")
        self.assertEqual(sr.fmt_ts(None), "")

    def test_urls(self):
        u = sr.listing_url("EnergyDrinks", "top", {"t": "year"},
                           after="t3_zz")
        self.assertIn("/r/EnergyDrinks/top.json?", u)
        self.assertIn("t=year", u)
        self.assertIn("after=t3_zz", u)
        self.assertIn("limit=100", u)
        self.assertIn("/comments/p1.json?", sr.comments_url("p1"))


# --------------------------------------------------------------------------
# build_external_datasets.py::build_reddit — glob patch
# --------------------------------------------------------------------------

def _write_rows(path, columns, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


class TestBuildRedditGlob(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.raw = os.path.join(self.tmp, "raw")
        self.data = os.path.join(self.tmp, "data")
        self.base = os.path.join(self.raw, "Reddit data", "r-Energy Drinks")
        os.makedirs(self.base)
        os.makedirs(os.path.join(self.data, "combined"))
        with open(os.path.join(self.data, "combined", "brand_summary.csv"),
                  "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["brand"])
            for b in ("Red Bull", "Monster", "Celsius"):
                w.writerow([b])
        self._old_raw, self._old_data = bed.RAW, bed.DATA
        bed.RAW, bed.DATA = self.raw, self.data

    def tearDown(self):
        bed.RAW, bed.DATA = self._old_raw, self._old_data
        shutil.rmtree(self.tmp)

    def _dated_pair(self, stamp, posts, comments):
        _write_rows(
            os.path.join(self.base, "energydrinks_posts_%s.csv" % stamp),
            sr.POST_COLUMNS, posts)
        _write_rows(
            os.path.join(self.base, "energydrinks_comments_%s.csv" % stamp),
            sr.COMMENT_COLUMNS, comments)

    def test_picks_newest_dated_files(self):
        # OLD export only mentions Monster — must be ignored
        self._dated_pair("20260609", [
            {"id": "o1", "title": "Monster haul", "selftext": "",
             "created_utc": "1749400000.0", "score": "1",
             "num_comments": "0", "permalink": "/r/x/o1/"},
        ], [
            {"id": "oc1", "link_id": "t3_o1", "body": "Monster forever",
             "created_utc": "1749400001.0", "score": "1"},
        ])
        # NEW export mentions Red Bull (post + comment) and Celsius
        self._dated_pair("20260706", [
            {"id": "n1", "title": "Red Bull is great", "selftext": "",
             "created_utc": "1751700000.0", "score": "5",
             "num_comments": "2", "permalink": "/r/x/n1/"},
        ], [
            {"id": "nc1", "link_id": "t3_n1", "body": "red bull all day",
             "created_utc": "1751700001.0", "score": "2"},
            {"id": "nc2", "link_id": "t3_n1", "body": "celsius made me crash",
             "created_utc": "1751700002.0", "score": "1"},
        ])

        bed.build_reddit()

        pulse = os.path.join(self.data, "reddit", "brand_pulse.csv")
        self.assertTrue(os.path.exists(pulse))
        with open(pulse, encoding="utf-8", newline="") as f:
            rows = {r["brand"]: r for r in csv.DictReader(f)}
        self.assertIn("Red Bull", rows)
        self.assertEqual(rows["Red Bull"]["mentions"], "2")
        self.assertIn("Celsius", rows)
        self.assertEqual(rows["Celsius"]["mentions"], "1")
        self.assertNotIn("Monster", rows)  # old export not read

        meta = os.path.join(self.data, "reddit", "meta.csv")
        with open(meta, encoding="utf-8", newline="") as f:
            kv = {r["key"]: r["value"] for r in csv.DictReader(f)}
        self.assertEqual(kv["posts"], "1")
        self.assertEqual(kv["comments"], "2")

    def test_clear_error_when_no_dated_files(self):
        # folder exists but holds no exports
        err = io.StringIO()
        old_stderr, sys.stderr = sys.stderr, err
        try:
            bed.build_reddit()  # must not raise
        finally:
            sys.stderr = old_stderr
        self.assertIn("scrape_reddit.py", err.getvalue())
        self.assertFalse(
            os.path.exists(os.path.join(self.data, "reddit",
                                        "brand_pulse.csv"))
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
