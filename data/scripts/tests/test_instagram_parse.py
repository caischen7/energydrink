import os
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
#!/usr/bin/env python3
"""Fixture tests for data/scripts/scrape_instagram.py (no network, no
instaloader import needed — the backend imports it lazily)."""

import csv
import datetime as dt
import importlib.util
import os
import tempfile
import unittest
from types import SimpleNamespace

SCRIPT = REPO + "/data/scripts/scrape_instagram.py"
REAL_CSV = REPO + "/data/instagram/posts.csv"

spec = importlib.util.spec_from_file_location("scrape_instagram", SCRIPT)
si = importlib.util.module_from_spec(spec)
spec.loader.exec_module(si)


def stub_post(shortcode="AbC12_-x", date=dt.datetime(2026, 7, 1, 15, 30),
              likes=1234, comments=56, caption="hello #World #energy"):
    return SimpleNamespace(shortcode=shortcode, date_utc=date, likes=likes,
                           comments=comments, caption=caption)


class TestHashtags(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(si.extract_hashtags("go #Fast now #fuel!"),
                         "#Fast #fuel")

    def test_dedupes_case_insensitive_keeps_first_spelling(self):
        self.assertEqual(si.extract_hashtags("#Energy #ENERGY #energy #zap"),
                         "#Energy #zap")

    def test_unicode_and_underscore_and_digits(self):
        self.assertEqual(si.extract_hashtags("x #día_1 y #café2"),
                         "#día_1 #café2")

    def test_none_and_empty_and_no_tags(self):
        self.assertEqual(si.extract_hashtags(None), "")
        self.assertEqual(si.extract_hashtags(""), "")
        self.assertEqual(si.extract_hashtags("no tags # here"), "")

    def test_punctuation_terminates_tag(self):
        self.assertEqual(si.extract_hashtags("#sugarfree, #crash-free."),
                         "#sugarfree #crash")


class TestPostRow(unittest.TestCase):
    def test_full_row(self):
        row = si.post_row(stub_post(), "Monster", "monsterenergy")
        self.assertEqual(row, {
            "brand": "Monster",
            "brand_username": "monsterenergy",
            "post_url": "https://www.instagram.com/p/AbC12_-x/",
            "post_date": "2026-07-01",
            "likes_count": 1234,
            "comments_count": 56,
            "caption": "hello #World #energy",
            "hashtags": "#World #energy",
        })
        self.assertEqual(list(row.keys()), si.POST_COLUMNS)

    def test_hidden_likes_and_missing_fields(self):
        row = si.post_row(stub_post(likes=-1, comments=None, caption=None,
                                    date=None),
                          "Celsius", "celsiusofficial")
        self.assertEqual(row["likes_count"], "")
        self.assertEqual(row["comments_count"], "")
        self.assertEqual(row["caption"], "")
        self.assertEqual(row["hashtags"], "")
        self.assertEqual(row["post_date"], "")

    def test_date_object_tolerated(self):
        row = si.post_row(stub_post(date=dt.date(2025, 12, 31)), "Zoa", "zoaenergy")
        self.assertEqual(row["post_date"], "2025-12-31")


class TestBrandMapping(unittest.TestCase):
    def test_all_default_accounts_map(self):
        expect = {
            "monsterenergy": "Monster", "celsiusofficial": "Celsius",
            "alaninutrition": "Alani Nu", "bangenergy": "Bang",
            "drinkprime": "Prime", "reignbodyfuel": "Reign",
            "rockstarenergy": "Rockstar", "zoaenergy": "Zoa",
        }
        for user in si.DEFAULT_ACCOUNTS:
            self.assertEqual(si.brand_for_username(user), expect[user])

    def test_substring_fallback(self):
        self.assertEqual(si.brand_for_username("ghostenergy"), "Ghost")
        self.assertEqual(si.brand_for_username("redbullracing"), "Red Bull")

    def test_unknown_passes_through(self):
        self.assertEqual(si.brand_for_username("someindiebrand"),
                         "someindiebrand")

    def test_norm_brand(self):
        self.assertEqual(si.norm_brand("  MONSTERENERGY "), "Monster")
        self.assertEqual(si.norm_brand("Nobody"), "Nobody")
        self.assertIsNone(si.norm_brand(""))


class TestShortcodeKey(unittest.TestCase):
    def test_all_committed_url_styles(self):
        for url in (
            "https://www.instagram.com/p/DB1a0c_PZv4/",
            "https://www.instagram.com/alaninutrition/p/DB1a0c_PZv4/",
            "https://www.instagram.com/micjanee/reel/DB1a0c_PZv4/",
            "https://www.instagram.com/tv/DB1a0c_PZv4/",
        ):
            self.assertEqual(si.shortcode_key(url), "DB1a0c_PZv4")

    def test_fallback_to_raw_url(self):
        self.assertEqual(si.shortcode_key("https://x.test/weird"),
                         "https://x.test/weird")
        self.assertEqual(si.shortcode_key(None), "")


class TestMerge(unittest.TestCase):
    def _old_rows(self):
        return [
            {"brand": "Alani Nu", "brand_username": "alaninutrition",
             "post_url": "https://www.instagram.com/alaninutrition/p/OLD1/",
             "post_date": "2024-11-01", "likes_count": "94000.0",
             "comments_count": "3557.0",
             "caption": "old caption\nwith newline", "hashtags": ""},
            {"brand": "Monster", "brand_username": "monsterenergy",
             "post_url": "https://www.instagram.com/monsterenergy/reel/KEEP2/",
             "post_date": "2025-01-05", "likes_count": "10",
             "comments_count": "2", "caption": "keep me", "hashtags": "#Snow"},
        ]

    def test_fresh_wins_old_survive_new_appended(self):
        new = [
            si.post_row(stub_post(shortcode="OLD1",
                                  date=dt.datetime(2024, 11, 1),
                                  likes=95000, comments=3600,
                                  caption="refreshed #Winter"),
                        "Alani Nu", "alaninutrition"),
            si.post_row(stub_post(shortcode="NEW3"), "Zoa", "zoaenergy"),
        ]
        merged = si.merge_rows(self._old_rows(), new)
        self.assertEqual([si.shortcode_key(r["post_url"]) for r in merged],
                         ["OLD1", "KEEP2", "NEW3"])
        self.assertEqual(merged[0]["likes_count"], 95000)  # fresh row won
        self.assertEqual(merged[0]["post_url"],
                         "https://www.instagram.com/p/OLD1/")
        self.assertEqual(merged[1]["caption"], "keep me")  # old-only survived

    def test_duplicate_shortcodes_collapse(self):
        old = self._old_rows() + [self._old_rows()[0]]  # dupe in old file
        new = [si.post_row(stub_post(shortcode="NEW3"), "Zoa", "zoaenergy")] * 2
        merged = si.merge_rows(old, new)
        self.assertEqual([si.shortcode_key(r["post_url"]) for r in merged],
                         ["OLD1", "KEEP2", "NEW3"])

    def test_roundtrip_through_csv(self):
        new = [si.post_row(stub_post(shortcode="NEW3",
                                     caption="line1\nline2 #tag"),
                           "Zoa", "zoaenergy")]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "posts.csv")
            si.write_csv(path, si.POST_COLUMNS,
                         si.merge_rows(self._old_rows(), new))
            with open(path, newline="", encoding="utf-8") as f:
                self.assertEqual(
                    f.readline().rstrip("\r\n"),
                    "brand,brand_username,post_url,post_date,likes_count,"
                    "comments_count,caption,hashtags")
            back = si.read_existing(path, si.POST_COLUMNS)
        self.assertEqual(len(back), 3)
        self.assertEqual(back[0]["caption"], "old caption\nwith newline")
        self.assertEqual(back[2]["caption"], "line1\nline2 #tag")

    def test_read_existing_missing_file(self):
        self.assertEqual(si.read_existing("/nonexistent/nope.csv",
                                          si.POST_COLUMNS), [])


class TestAgainstCommittedFile(unittest.TestCase):
    """The real repo CSV must survive a merge unchanged (read-only test)."""

    def test_header_matches_schema(self):
        with open(REAL_CSV, newline="", encoding="utf-8") as f:
            self.assertEqual(next(csv.reader(f)), si.POST_COLUMNS)

    def test_all_committed_rows_survive_noop_merge(self):
        old = si.read_existing(REAL_CSV, si.POST_COLUMNS)
        self.assertGreater(len(old), 0)
        merged = si.merge_rows(old, [])
        self.assertEqual(merged, old)  # nothing lost, order kept

    def test_fresh_rescrape_of_committed_post_replaces_it(self):
        old = si.read_existing(REAL_CSV, si.POST_COLUMNS)
        code = si.shortcode_key(old[0]["post_url"])
        fresh = si.post_row(stub_post(shortcode=code), "Alani Nu",
                            "alaninutrition")
        merged = si.merge_rows(old, [fresh])
        self.assertEqual(len(merged), len(old))
        self.assertEqual(merged[0], fresh)


if __name__ == "__main__":
    unittest.main(verbosity=2)
