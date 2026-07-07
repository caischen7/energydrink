import os
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
"""Offline fixture tests for data/scripts/scrape_tiktok.py (no network)."""
import importlib.util
import tempfile
import unittest

SCRIPT = os.path.join(REPO, "data", "scripts", "scrape_tiktok.py")
spec = importlib.util.spec_from_file_location("scrape_tiktok", SCRIPT)
tk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tk)


ITEM = {
    "id": "7311122233344455566",
    "desc": "New CELSIUS flavor drop #energydrink #celsius",
    "createTime": 1782000000,
    "author": {"uniqueId": "celsiusofficial", "nickname": "CELSIUS"},
    "stats": {"playCount": 1200000, "diggCount": 45000,
              "commentCount": 812, "shareCount": 900, "collectCount": 3100},
    "textExtra": [{"hashtagName": "fyp"}],
}


class TestHarvestVideos(unittest.TestCase):
    def test_profile_item(self):
        blob = {"ItemModule": {"7311122233344455566": ITEM}}
        rows = tk.harvest_videos([blob], "@celsiusofficial")
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["video_id"], "7311122233344455566")
        self.assertEqual(r["author"], "celsiusofficial")
        self.assertEqual(r["plays"], 1200000)
        self.assertEqual(r["likes"], 45000)
        self.assertEqual(r["saves"], 3100)
        self.assertEqual(r["create_date"], "2026-06-21")
        self.assertIn("#energydrink", r["hashtags"])
        self.assertIn("#fyp", r["hashtags"])  # textExtra merged in
        self.assertIn("Celsius", r["brands_mentioned"])
        self.assertEqual(
            r["url"],
            "https://www.tiktok.com/@celsiusofficial/video/7311122233344455566")
        self.assertEqual(set(r), set(tk.VIDEO_COLUMNS))

    def test_statsV2_strings(self):
        item = dict(ITEM, stats=None,
                    statsV2={"playCount": "1900000", "diggCount": "52000",
                             "commentCount": "77", "shareCount": "12",
                             "collectCount": "5"})
        item = {k: v for k, v in item.items() if v is not None}
        rows = tk.harvest_videos([{"itemList": [item]}], "#energydrink")
        self.assertEqual(rows[0]["plays"], 1900000)

    def test_dedupe_across_blobs_and_non_videos_skipped(self):
        junk = {"id": "not-digits", "desc": "x", "stats": {}}
        rows = tk.harvest_videos(
            [{"a": [ITEM, junk]}, {"b": ITEM}], "@celsiusofficial")
        self.assertEqual(len(rows), 1)

    def test_dict_without_stats_is_not_a_video(self):
        d = {"id": "123456", "desc": "hello"}
        self.assertEqual(tk.harvest_videos([d], "s"), [])


class TestHarvestComments(unittest.TestCase):
    BLOB = {"comments": [{
        "cid": "9988776655",
        "text": "no crash at all, love it",
        "digg_count": 41,
        "create_time": 1782000000,
        "user": {"unique_id": "somefan123"},
    }]}

    def test_comment_fields(self):
        rows = tk.harvest_comments([self.BLOB, self.BLOB], "731")
        self.assertEqual(len(rows), 1)  # deduped on cid
        r = rows[0]
        self.assertEqual(r["comment_id"], "9988776655")
        self.assertEqual(r["comment_likes"], 41)
        self.assertEqual(r["comment_date"], "2026-06-21")
        self.assertEqual(r["author"], "somefan123")
        self.assertEqual(set(r), set(tk.COMMENT_COLUMNS))


class TestHelpers(unittest.TestCase):
    def test_abbreviated_counts(self):
        self.assertEqual(tk.to_int("1.2M"), 1200000)
        self.assertEqual(tk.to_int("47K"), 47000)
        self.assertEqual(tk.to_int("903"), 903)
        self.assertEqual(tk.to_int(903), 903)
        self.assertIsNone(tk.to_int("N/A"))
        self.assertIsNone(tk.to_int({"x": 1}))

    def test_brands_mentioned_word_boundaries(self):
        self.assertIn("Celsius", tk.brands_mentioned("love celsius live fit"))
        self.assertIn("Red Bull", tk.brands_mentioned("redbull gives wings"))
        self.assertEqual(tk.brands_mentioned("primetime television"), "")

    def test_merge_fresh_wins(self):
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "videos.csv")
        row = {c: "" for c in tk.VIDEO_COLUMNS}
        old = dict(row, video_id="1", desc="old")
        tk.write_csv(path, tk.VIDEO_COLUMNS, [old])
        cols, merged = tk.merge_rows(
            path, tk.VIDEO_COLUMNS,
            [dict(row, video_id="1", desc="new"),
             dict(row, video_id="2", desc="other")], "video_id")
        self.assertEqual(len(merged), 2)
        self.assertEqual(
            {r["video_id"]: r["desc"] for r in merged}["1"], "new")


if __name__ == "__main__":
    unittest.main(verbosity=1)
