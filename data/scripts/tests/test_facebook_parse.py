import os
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
"""Offline fixture tests for data/scripts/scrape_facebook.py (no network)."""
import importlib.util
import tempfile
import unittest

SCRIPT = os.path.join(REPO, "data", "scripts", "scrape_facebook.py")
spec = importlib.util.spec_from_file_location("scrape_facebook", SCRIPT)
fb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fb)


AD = {
    "adArchiveID": "1234567890",
    "isActive": True,
    "startDate": 1781136000,
    "endDate": None,
    "publisherPlatform": ["FACEBOOK", "INSTAGRAM"],
    "snapshot": {
        "page_name": "CELSIUS Energy Drink",
        "body": {"text": "LIVE FIT. Zero sugar essential energy."},
        "cta_text": "Shop Now",
        "cards": [{"body": "Try the new flavor."}],
    },
}


class TestHarvestAds(unittest.TestCase):
    def test_ad_fields(self):
        rows = fb.harvest_ads([{"payload": {"results": [[AD]]}}], "Celsius")
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["ad_id"], "1234567890")
        self.assertEqual(r["brand"], "Celsius")       # from page_name
        self.assertEqual(r["page_name"], "CELSIUS Energy Drink")
        self.assertIn("LIVE FIT", r["ad_text"])
        self.assertIn("Try the new flavor.", r["ad_text"])
        self.assertEqual(r["cta"], "Shop Now")
        self.assertEqual(r["start_date"], "2026-06-11")
        self.assertIsNone(r["end_date"])
        self.assertTrue(r["active"])
        self.assertEqual(r["platforms"], "FACEBOOK; INSTAGRAM")
        self.assertEqual(
            r["snapshot_url"],
            "https://www.facebook.com/ads/library/?id=1234567890")
        self.assertEqual(set(r), set(fb.AD_COLUMNS))

    def test_snake_case_variant_and_creative_bodies(self):
        ad = {
            "ad_archive_id": 777,
            "is_active": False,
            "start_date": 1781136000,
            "ad_creative_bodies": ["Fuel your day."],
            "publisher_platforms": ["INSTAGRAM"],
            "page_name": "Alani Nu",
        }
        rows = fb.harvest_ads([ad], "Alani Nu")
        r = rows[0]
        self.assertEqual(r["ad_id"], "777")
        self.assertEqual(r["brand"], "Alani Nu")
        self.assertIn("Fuel your day.", r["ad_text"])
        self.assertFalse(r["active"])
        self.assertEqual(r["platforms"], "INSTAGRAM")

    def test_dedupe_and_junk_rejection(self):
        rows = fb.harvest_ads([{"a": AD}, {"b": AD},
                               {"noise": {"foo": "bar"}}], "Celsius")
        self.assertEqual(len(rows), 1)

    def test_brand_falls_back_to_query(self):
        ad = dict(AD, adArchiveID="2", snapshot={"page_name": "Some Fan Page"})
        rows = fb.harvest_ads([ad], "Ghost Energy")
        self.assertEqual(rows[0]["brand"], "Ghost")


class TestHelpers(unittest.TestCase):
    def test_ad_text_dedupes_and_caps(self):
        snap = {"body": {"text": "Same line"}, "cards": [{"body": "Same line"},
                                                         {"body": "Other"}]}
        text = fb._ad_text_of(snap)
        self.assertEqual(text.count("Same line"), 1)
        self.assertIn("Other", text)

    def test_unix_date(self):
        self.assertEqual(fb.unix_date(1781136000), "2026-06-11")
        self.assertIsNone(fb.unix_date("not-a-ts"))

    def test_merge_fresh_wins(self):
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "ads.csv")
        row = {c: "" for c in fb.AD_COLUMNS}
        fb.write_csv(path, fb.AD_COLUMNS, [dict(row, ad_id="1", cta="old")])
        cols, merged = fb.merge_rows(
            path, fb.AD_COLUMNS,
            [dict(row, ad_id="1", cta="new"), dict(row, ad_id="2")], "ad_id")
        self.assertEqual(len(merged), 2)
        self.assertEqual({r["ad_id"]: r["cta"] for r in merged}["1"], "new")


if __name__ == "__main__":
    unittest.main(verbosity=1)
