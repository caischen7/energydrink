import os
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
#!/usr/bin/env python3
"""Fixture tests for data/scripts/scrape_youtube.py — every parser/transform,
no network. Run:  python3 test_youtube_parse.py"""

import csv
import importlib.util
import os
import tempfile
import unittest

SCRIPT = REPO + "/data/scripts/scrape_youtube.py"
_spec = importlib.util.spec_from_file_location("scrape_youtube", SCRIPT)
sy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sy)

HERE = os.path.dirname(os.path.abspath(__file__))


# --------------------------------------------------------------------------
# Fixtures — realistic minimal API payloads
# --------------------------------------------------------------------------

SEARCH_PAGE = {
    "kind": "youtube#searchListResponse",
    "etag": "abc",
    "nextPageToken": "CDIQAA",
    "regionCode": "US",
    "pageInfo": {"totalResults": 1000000, "resultsPerPage": 50},
    "items": [
        {"kind": "youtube#searchResult",
         "id": {"kind": "youtube#video", "videoId": "abc123XYZ_0"}},
        {"kind": "youtube#searchResult",
         "id": {"kind": "youtube#video", "videoId": "def456XYZ_1"}},
        # a channel result sneaks in — must be skipped (no videoId)
        {"kind": "youtube#searchResult",
         "id": {"kind": "youtube#channel", "channelId": "UCxyz"}},
    ],
}

VIDEOS_PAGE = {
    "kind": "youtube#videoListResponse",
    "items": [
        {
            "kind": "youtube#video",
            "id": "abc123XYZ_0",
            "snippet": {
                "publishedAt": "2024-11-02T15:04:05Z",
                "channelId": "UCcaffeine",
                "title": "CELSIUS vs Red Bull: the ULTIMATE taste test",
                "description": "We also try Ghost.\nThis is not a monster "
                               "truck video.\nLinks below!",
                "channelTitle": "Caffeine Lab",
                "tags": ["energy drink", "celsius", "red bull"],
                "categoryId": "24",
            },
            "contentDetails": {"duration": "PT12M34S", "definition": "hd"},
            "statistics": {"viewCount": "15342", "likeCount": "823",
                           "favoriteCount": "0", "commentCount": "197"},
        },
        {
            "kind": "youtube#video",
            "id": "def456XYZ_1",
            "snippet": {
                "publishedAt": "2023-01-09T00:00:00Z",
                "title": "quiet video with hidden likes",
                "description": "",
                "channelTitle": "smallchannel",
                "categoryId": "99",  # unknown id → passes through raw
                # no "tags" key at all
            },
            "contentDetails": {"duration": "PT45S"},
            "statistics": {"viewCount": "10"},  # likes/comments hidden
        },
    ],
}

COMMENTS_PAGE = {
    "kind": "youtube#commentThreadListResponse",
    "nextPageToken": "QURTSl9p",
    "items": [
        {
            "kind": "youtube#commentThread",
            "id": "UgwThread1",
            "snippet": {
                "videoId": "abc123XYZ_0",
                "topLevelComment": {
                    "kind": "youtube#comment",
                    "id": "UgwThread1",
                    "snippet": {
                        "authorDisplayName": "@caffeinefan",
                        "textDisplay": "Ghost legend is the GOAT",
                        "likeCount": 12,
                        "publishedAt": "2024-12-25T10:00:00Z",
                    },
                },
                "totalReplyCount": 1,
            },
            "replies": {
                "comments": [
                    {
                        "kind": "youtube#comment",
                        "id": "UgwThread1.Reply1",
                        "snippet": {
                            "authorDisplayName": "@skeptic",
                            "textDisplay": "the prime minister of energy lol",
                            "likeCount": 0,
                            "publishedAt": "2024-12-26T11:30:00Z",
                        },
                    }
                ]
            },
        },
        {   # a thread with no replies key
            "kind": "youtube#commentThread",
            "id": "UgwThread2",
            "snippet": {
                "videoId": "abc123XYZ_0",
                "topLevelComment": {
                    "id": "UgwThread2",
                    "snippet": {
                        "authorDisplayName": "@lurker",
                        "textDisplay": "too sweet for me",
                        "likeCount": 3,
                        "publishedAt": "2025-01-02T08:00:00Z",
                    },
                },
                "totalReplyCount": 0,
            },
        },
    ],
}

YTDLP_INFO = {
    "id": "zz9pluralZa",
    "title": "Alani Nu vs Celsius: which is better?",
    "description": "sipping on alani nu today. gfuel next week",
    "channel": "Sip Review",
    "uploader": "Sip Review Uploads",
    "upload_date": "20250314",
    "duration": 615,
    "view_count": 4321,
    "like_count": 210,
    "comment_count": 33,
    "tags": ["alani nu", "celsius"],
    "categories": ["Howto & Style"],
    "webpage_url": "https://www.youtube.com/watch?v=zz9pluralZa",
    "comments": [
        {"id": "UgX1", "author": "@fan", "text": "the pink one slaps",
         "like_count": 4, "timestamp": 1741912345, "parent": "root"},
        {"id": "UgX1.r1", "author": "@hater", "text": "too sweet",
         "like_count": 0, "timestamp": None, "parent": "UgX1"},
    ],
}


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------

class TestSchemas(unittest.TestCase):
    def test_video_columns_match_committed_header(self):
        self.assertEqual(sy.VIDEO_COLUMNS, [
            "source", "search_query", "video_id", "title", "channel",
            "upload_date", "duration_seconds", "view_count", "like_count",
            "comment_count", "description", "tags", "categories", "url",
            "transcript", "brands_mentioned"])

    def test_comment_columns_match_committed_header(self):
        self.assertEqual(sy.COMMENT_COLUMNS, [
            "source", "video_id", "comment_id", "author", "comment",
            "comment_likes", "comment_date"])


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

class TestDuration(unittest.TestCase):
    def test_hms(self):
        self.assertEqual(sy.duration_seconds("PT1H2M3S"), 3723)

    def test_seconds_only(self):
        self.assertEqual(sy.duration_seconds("PT45S"), 45)

    def test_minutes_only(self):
        self.assertEqual(sy.duration_seconds("PT2M"), 120)

    def test_hours_only(self):
        self.assertEqual(sy.duration_seconds("PT1H"), 3600)

    def test_days(self):
        self.assertEqual(sy.duration_seconds("P1DT2H"), 93600)

    def test_live_stream_zero(self):
        self.assertEqual(sy.duration_seconds("P0D"), 0)

    def test_empty_and_garbage(self):
        self.assertEqual(sy.duration_seconds(""), "")
        self.assertEqual(sy.duration_seconds(None), "")
        self.assertEqual(sy.duration_seconds("12:34"), "")


class TestIsoDate(unittest.TestCase):
    def test_rfc3339(self):
        self.assertEqual(sy.iso_date("2024-11-02T15:04:05Z"), "2024-11-02")

    def test_ytdlp_compact(self):
        self.assertEqual(sy.iso_date("20230115"), "2023-01-15")

    def test_empty_and_raw(self):
        self.assertEqual(sy.iso_date(""), "")
        self.assertEqual(sy.iso_date(None), "")
        self.assertEqual(sy.iso_date("last Tuesday"), "last Tuesday")


class TestCategoryMap(unittest.TestCase):
    def test_known_ids(self):
        self.assertEqual(sy.category_name("24"), "Entertainment")
        self.assertEqual(sy.category_name(26), "Howto & Style")
        self.assertEqual(sy.category_name("17"), "Sports")
        self.assertEqual(sy.category_name("28"), "Science & Technology")

    def test_unknown_id_passes_through(self):
        self.assertEqual(sy.category_name("99"), "99")
        self.assertEqual(sy.category_name(None), "")


class TestBrandsMentioned(unittest.TestCase):
    def test_basic_multi_brand_sorted(self):
        self.assertEqual(
            sy.brands_mentioned("Celsius vs Red Bull vs GHOST taste test"),
            "Celsius, Ghost, Red Bull")

    def test_title_plus_description(self):
        self.assertEqual(
            sy.brands_mentioned("morning routine", "I drink REIGN and zoa"),
            "Reign, Zoa")

    def test_case_insensitive(self):
        self.assertEqual(sy.brands_mentioned("MONSTER energy!!"), "Monster")

    def test_monster_truck_matches_by_design(self):
        # Known, accepted false positive — consistent with the alias matching
        # in build_clean_datasets/build_external_datasets; the dashboard's
        # noise filter compensates downstream.
        self.assertEqual(sy.brands_mentioned("monster truck rally"), "Monster")

    def test_prime_minister_matches_by_design(self):
        self.assertEqual(sy.brands_mentioned("the prime minister speaks"),
                         "Prime")

    def test_word_boundaries_hold(self):
        self.assertEqual(sy.brands_mentioned("nostalgia for bangers"), "")
        self.assertEqual(sy.brands_mentioned("primetime television"), "")
        self.assertEqual(sy.brands_mentioned("ghostly reigning champion"), "")
        self.assertEqual(sy.brands_mentioned("c40 engine specs"), "")

    def test_nos_needs_boundary(self):
        self.assertEqual(sy.brands_mentioned("NOS at the drag strip"), "NOS")
        self.assertEqual(sy.brands_mentioned("nose to the grindstone"), "")

    def test_dotted_alias(self):
        self.assertEqual(sy.brands_mentioned("I love Liquid I.V. so much"),
                         "Liquid I.V.")

    def test_alias_variants_collapse_to_one_canonical(self):
        self.assertEqual(sy.brands_mentioned("alani and Alani Nu together"),
                         "Alani Nu")

    def test_five_hour(self):
        self.assertEqual(sy.brands_mentioned("5 hour energy shot review"),
                         "5-hour Energy")

    def test_empty(self):
        self.assertEqual(sy.brands_mentioned("", None), "")


# --------------------------------------------------------------------------
# API payload parsers
# --------------------------------------------------------------------------

class TestApiSearch(unittest.TestCase):
    def test_ids_and_token(self):
        ids, token = sy.api_search_ids(SEARCH_PAGE)
        self.assertEqual(ids, ["abc123XYZ_0", "def456XYZ_1"])
        self.assertEqual(token, "CDIQAA")

    def test_last_page_no_token(self):
        ids, token = sy.api_search_ids({"items": []})
        self.assertEqual(ids, [])
        self.assertIsNone(token)


class TestApiVideoRow(unittest.TestCase):
    def test_full_row(self):
        row = sy.api_video_row(VIDEOS_PAGE["items"][0], "energy drink review")
        self.assertEqual(row, {
            "source": "api_v3",
            "search_query": "energy drink review",
            "video_id": "abc123XYZ_0",
            "title": "CELSIUS vs Red Bull: the ULTIMATE taste test",
            "channel": "Caffeine Lab",
            "upload_date": "2024-11-02",
            "duration_seconds": 754,
            "view_count": 15342,
            "like_count": 823,
            "comment_count": 197,
            "description": "We also try Ghost.\nThis is not a monster "
                           "truck video.\nLinks below!",
            "tags": "energy drink; celsius; red bull",
            "categories": "Entertainment",
            "url": "https://www.youtube.com/watch?v=abc123XYZ_0",
            "transcript": "",
            # Monster from "monster truck" is the documented false positive
            "brands_mentioned": "Celsius, Ghost, Monster, Red Bull",
        })

    def test_missing_stats_and_tags(self):
        row = sy.api_video_row(VIDEOS_PAGE["items"][1], "best energy drink")
        self.assertEqual(row["view_count"], 10)
        self.assertIsNone(row["like_count"])     # hidden → blank in the CSV
        self.assertIsNone(row["comment_count"])
        self.assertEqual(row["tags"], "")
        self.assertEqual(row["categories"], "99")
        self.assertEqual(row["duration_seconds"], 45)
        self.assertEqual(row["brands_mentioned"], "")
        self.assertEqual(row["transcript"], "")


class TestApiCommentRows(unittest.TestCase):
    def test_top_level_and_replies(self):
        rows = sy.api_comment_rows(COMMENTS_PAGE, "abc123XYZ_0")
        self.assertEqual(len(rows), 3)  # 2 top-level + 1 reply
        self.assertEqual(rows[0], {
            "source": "api_v3",
            "video_id": "abc123XYZ_0",
            "comment_id": "UgwThread1",
            "author": "@caffeinefan",
            "comment": "Ghost legend is the GOAT",
            "comment_likes": 12,
            "comment_date": "2024-12-25",
        })
        self.assertEqual(rows[1]["comment_id"], "UgwThread1.Reply1")
        self.assertEqual(rows[1]["comment"], "the prime minister of energy lol")
        self.assertEqual(rows[1]["comment_likes"], 0)
        self.assertEqual(rows[1]["comment_date"], "2024-12-26")
        self.assertEqual(rows[2]["comment_id"], "UgwThread2")

    def test_empty_page(self):
        self.assertEqual(sy.api_comment_rows({"items": []}, "x"), [])


class TestApiErrorReason(unittest.TestCase):
    def test_quota_exceeded(self):
        body = ('{"error": {"code": 403, "message": "quota", "errors": '
                '[{"reason": "quotaExceeded", "domain": "youtube.quota"}]}}')
        self.assertEqual(sy.api_error_reason(body), "quotaExceeded")

    def test_comments_disabled(self):
        body = ('{"error": {"code": 403, "errors": '
                '[{"reason": "commentsDisabled"}]}}')
        self.assertEqual(sy.api_error_reason(body), "commentsDisabled")

    def test_new_style_details(self):
        body = ('{"error": {"code": 403, "status": "PERMISSION_DENIED", '
                '"details": [{"reason": "API_KEY_INVALID"}]}}')
        self.assertEqual(sy.api_error_reason(body), "API_KEY_INVALID")

    def test_garbage(self):
        self.assertEqual(sy.api_error_reason("<html>nope</html>"), "")


class TestQuotaEstimate(unittest.TestCase):
    def test_defaults(self):
        # 8 queries × 1 search page × 100 + ceil(400/50) video calls
        # + 8×50×2 comment pages = 800 + 8 + 800
        self.assertEqual(sy.quota_estimate(8, 50, 2), 1608)

    def test_multi_search_pages(self):
        # 120 videos/query → 3 search pages each
        self.assertEqual(sy.quota_estimate(1, 120, 1),
                         3 * 100 + 3 + 120)


# --------------------------------------------------------------------------
# yt-dlp info-dict mapping
# --------------------------------------------------------------------------

class TestYtdlpMapping(unittest.TestCase):
    def test_video_row(self):
        row = sy.ytdlp_video_row(YTDLP_INFO, "Alani Nu energy drink")
        self.assertEqual(row, {
            "source": "yt_dlp",
            "search_query": "Alani Nu energy drink",
            "video_id": "zz9pluralZa",
            "title": "Alani Nu vs Celsius: which is better?",
            "channel": "Sip Review",
            "upload_date": "2025-03-14",
            "duration_seconds": 615,
            "view_count": 4321,
            "like_count": 210,
            "comment_count": 33,
            "description": "sipping on alani nu today. gfuel next week",
            "tags": "alani nu; celsius",
            "categories": "Howto & Style",
            "url": "https://www.youtube.com/watch?v=zz9pluralZa",
            "transcript": "",
            "brands_mentioned": "Alani Nu, Celsius, G Fuel",
        })

    def test_uploader_fallback_and_missing_fields(self):
        info = {"id": "vid2", "title": "t", "uploader": "Fallback Name"}
        row = sy.ytdlp_video_row(info, "q")
        self.assertEqual(row["channel"], "Fallback Name")
        self.assertEqual(row["upload_date"], "")
        self.assertIsNone(row["view_count"])
        self.assertEqual(row["tags"], "")
        self.assertEqual(row["categories"], "")

    def test_comment_rows(self):
        rows = sy.ytdlp_comment_rows(YTDLP_INFO)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {
            "source": "yt_dlp",
            "video_id": "zz9pluralZa",
            "comment_id": "UgX1",
            "author": "@fan",
            "comment": "the pink one slaps",
            "comment_likes": 4,
            "comment_date": "2025-03-14",  # 1741912345 UTC
        })
        self.assertEqual(rows[1]["comment_date"], "")  # no timestamp
        self.assertEqual(rows[1]["comment_likes"], 0)

    def test_no_comments_key(self):
        self.assertEqual(sy.ytdlp_comment_rows({"id": "x"}), [])


# --------------------------------------------------------------------------
# Incremental merge
# --------------------------------------------------------------------------

def _comment(cid, text, source="api_v3"):
    return {"source": source, "video_id": "v1", "comment_id": cid,
            "author": "@a", "comment": text, "comment_likes": 1,
            "comment_date": "2025-01-01"}


class TestMergeRows(unittest.TestCase):
    def test_fresh_wins_order_kept_new_appended(self):
        old = [_comment("A", "old A"), _comment("B", "old B"),
               _comment("B", "dupe B in old file")]
        new = [_comment("A", "NEW A"), _comment("C", "new C")]
        merged = list(sy.merge_rows(iter(old), new, "comment_id"))
        self.assertEqual([r["comment_id"] for r in merged], ["A", "B", "C"])
        self.assertEqual(merged[0]["comment"], "NEW A")   # fresh row won
        self.assertEqual(merged[1]["comment"], "old B")   # untouched
        self.assertEqual(merged[2]["comment"], "new C")   # appended after

    def test_duplicate_keys_within_new_rows(self):
        new = [_comment("X", "first"), _comment("X", "second")]
        merged = list(sy.merge_rows(iter([]), new, "comment_id"))
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["comment"], "second")  # last write wins

    def test_empty_key_rows_pass_through(self):
        old = [_comment("", "keyless old"), _comment("A", "old A")]
        merged = list(sy.merge_rows(iter(old), [], "comment_id"))
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0]["comment"], "keyless old")


class TestWriteCsvMerged(unittest.TestCase):
    def test_file_roundtrip_merge(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            path = os.path.join(tmp, "comments.csv")
            # seed an "existing" file, as if from the original paid export
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=sy.COMMENT_COLUMNS)
                w.writeheader()
                w.writerow(_comment("old1", "kept as-is",
                                    source="overnight_12hr"))
                w.writerow(_comment("both", "stale text",
                                    source="overnight_12hr"))
            new = [_comment("both", "refreshed text"),
                   _comment("new1", "brand new")]
            sy.write_csv_merged(path, sy.COMMENT_COLUMNS, new, "comment_id")

            with open(path, newline="", encoding="utf-8") as f:
                header = next(csv.reader(f))
            with open(path, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(header, sy.COMMENT_COLUMNS)  # exact schema
            self.assertEqual([r["comment_id"] for r in rows],
                             ["old1", "both", "new1"])
            self.assertEqual(rows[0]["source"], "overnight_12hr")
            self.assertEqual(rows[1]["comment"], "refreshed text")
            self.assertEqual(rows[1]["source"], "api_v3")

    def test_no_existing_file(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            path = os.path.join(tmp, "videos.csv")
            row = sy.api_video_row(VIDEOS_PAGE["items"][0], "q")
            sy.write_csv_merged(path, sy.VIDEO_COLUMNS, [row], "video_id")
            with open(path, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["video_id"], "abc123XYZ_0")
            self.assertEqual(rows[0]["like_count"], "823")
            # None (hidden likes) must serialize as empty, not "None"
            row2 = sy.api_video_row(VIDEOS_PAGE["items"][1], "q")
            sy.write_csv_merged(path, sy.VIDEO_COLUMNS, [row2], "video_id")
            with open(path, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[1]["like_count"], "")


# --------------------------------------------------------------------------
# Brand helpers copied verbatim from scrape_walmart.py
# --------------------------------------------------------------------------

class TestBrandHelpers(unittest.TestCase):
    def test_norm_brand(self):
        self.assertEqual(sy.norm_brand("redbull"), "Red Bull")
        self.assertEqual(sy.norm_brand("  MONSTER "), "Monster")
        self.assertEqual(sy.norm_brand("Unknown Co"), "Unknown Co")
        self.assertIsNone(sy.norm_brand(None))

    def test_brand_from_title_longest_alias_wins(self):
        self.assertEqual(sy.brand_from_title("Red Bull 12 pack"), "Red Bull")
        self.assertEqual(sy.brand_from_title("Alani Nu Cosmic Stardust"),
                         "Alani Nu")
        self.assertIsNone(sy.brand_from_title("Generic Cola"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
