import os
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
"""Offline fixture tests for data/scripts/scrape_retailers.py (no network)."""
import importlib.util
import sys
import tempfile
import unittest

SCRIPT = os.path.join(REPO, "data", "scripts", "scrape_retailers.py")
spec = importlib.util.spec_from_file_location("scrape_retailers", SCRIPT)
sr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sr)


class TestTargetHarvest(unittest.TestCase):
    """Target-style search API payload (redsky plp_search_v2 shape)."""

    BLOB = {"data": {"search": {"products": [{
        "tcin": "78025960",
        "item": {
            "product_description": {"title": "Red Bull Energy Drink - 12pk/8.4 fl oz Cans"},
            "enrichment": {"buy_url": "https://www.target.com/p/red-bull/-/A-78025960"},
            "primary_brand": {"name": "Red Bull"},
        },
        "price": {"current_retail": 18.99, "reg_retail": 20.49},
        "ratings_and_reviews": {"statistics": {"rating": {"average": 4.8, "count": 2711}}},
    }]}}}

    def test_product_fields(self):
        rows = sr.harvest_products([self.BLOB], sr.RETAILERS["target"],
                                   "energy drink", "target")
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["item_id"], "78025960")
        self.assertEqual(r["retailer"], "target")
        self.assertIn("Red Bull", r["title"])
        self.assertEqual(r["brand"], "Red Bull")
        self.assertEqual(r["price_usd"], 18.99)
        self.assertEqual(r["list_price_usd"], 20.49)
        self.assertEqual(r["rating"], 4.8)
        self.assertEqual(r["link"],
                         "https://www.target.com/p/red-bull/-/A-78025960")
        self.assertEqual(set(r), set(sr.PRODUCT_COLUMNS))

    def test_dedupes_same_tcin_across_blobs(self):
        rows = sr.harvest_products([self.BLOB, self.BLOB],
                                   sr.RETAILERS["target"], "energy drink",
                                   "target")
        self.assertEqual(len(rows), 1)


class TestTraderJoesHarvest(unittest.TestCase):
    """TJ GraphQL-ish payload: sku + item_title + retail_price."""

    BLOB = {"data": {"products": {"items": [{
        "sku": "082716",
        "item_title": "Yerba Mate Energy Drink",
        "retail_price": "2.49",
        "url_key": "yerba-mate-energy-drink",
    }]}}}

    def test_product_fields(self):
        rows = sr.harvest_products([self.BLOB], sr.RETAILERS["traderjoes"],
                                   "energy drink", "traderjoes")
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["item_id"], "082716")
        self.assertEqual(r["price_usd"], 2.49)
        # url_template fallback used when no link is harvested
        self.assertEqual(
            r["link"], "https://www.traderjoes.com/home/products/pdp/082716")


class TestLdJsonFallback(unittest.TestCase):
    """schema.org Product markup — the retailer-agnostic fallback
    (Costco / Publix / Whole Foods often expose this)."""

    BLOB = {
        "@context": "https://schema.org",
        "@type": "Product",
        "sku": "1628286",
        "name": "Celsius Sparkling Energy Drink, Variety Pack, 12 fl oz, 18-count",
        "brand": {"@type": "Brand", "name": "celsius"},
        "offers": {"@type": "Offer", "price": "22.99"},
        "aggregateRating": {"ratingValue": "4.6", "reviewCount": "913"},
        "url": "https://www.costco.com/celsius-variety.product.1628286.html",
    }

    def test_product_fields(self):
        rows = sr.harvest_products([self.BLOB], sr.RETAILERS["costco"],
                                   "Celsius energy drink", "costco")
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["item_id"], "1628286")
        self.assertEqual(r["brand"], "Celsius")   # normalized via aliases
        self.assertEqual(r["price_usd"], 22.99)
        self.assertEqual(r["rating"], 4.6)
        self.assertEqual(r["reviews_total"], 913)
        self.assertIn("costco.com", r["link"])


class TestJunkRejection(unittest.TestCase):
    def test_nav_junk_without_commercial_signal_is_skipped(self):
        blob = {"menu": [{"id": "nav-1", "title": "Grocery"},
                         {"id": "nav-2", "title": "Beverages"}]}
        rows = sr.harvest_products([blob], sr.RETAILERS["publix"],
                                   "energy drink", "publix")
        self.assertEqual(rows, [])

    def test_product_like_dict_with_price_is_kept(self):
        blob = {"results": [{"productId": "abc-9",
                             "name": "ZOA Zero Sugar Energy Drink 12oz",
                             "price": {"amount": 2.79}}]}
        rows = sr.harvest_products([blob], sr.RETAILERS["publix"],
                                   "energy drink", "publix")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["price_usd"], 2.79)
        self.assertEqual(rows[0]["brand"], "Zoa")


class TestBazaarvoiceReviews(unittest.TestCase):
    PRODUCT = {"retailer": "costco", "item_id": "1628286", "brand": "Celsius",
               "title": "Celsius Variety Pack", "search_term": "Celsius energy drink"}
    BLOB = {"Results": [{
        "Id": "bv-321",
        "Rating": 5,
        "Title": "Great flavor",
        "ReviewText": "No crash and tastes amazing cold.",
        "SubmissionTime": "2026-06-21T14:03:00.000+00:00",
        "IsVerifiedPurchaser": True,
        "TotalPositiveFeedbackCount": 7,
    }], "TotalResults": 913}

    def test_review_fields(self):
        rows = sr.harvest_reviews([self.BLOB], self.PRODUCT,
                                  "Celsius energy drink")
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["review_id"], "bv-321")
        self.assertEqual(r["rating"], 5.0)
        self.assertEqual(r["review_date"], "2026-06-21")
        self.assertTrue(r["verified_purchase"])
        self.assertEqual(r["helpful_votes"], 7)
        self.assertEqual(set(r), set(sr.REVIEW_COLUMNS))

    def test_target_r2d2_style_and_dedupe(self):
        blob = {"reviews": [{
            "id": "tgt-1", "rating": 4, "title": "Good",
            "text": "Solid value twelve pack.",
            "submission_date": "2026-05-02T00:00:00Z",
        }]}
        rows = sr.harvest_reviews([blob, blob], self.PRODUCT, "energy drink")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["review_date"], "2026-05-02")

    def test_textless_or_unrated_dicts_are_not_reviews(self):
        blob = {"widgets": [{"text": "Sponsored", "position": 3},
                            {"ReviewText": "hi"}]}  # no rating
        self.assertEqual(
            sr.harvest_reviews([blob], self.PRODUCT, "energy drink"), [])


class TestKrogerApi(unittest.TestCase):
    DATA = {"productId": "0001111041660",
            "upc": "0001111041660",
            "description": "Monster Energy Original, 4 Cans",
            "brand": "Monster",
            "items": [{"price": {"regular": 7.99, "promo": 6.49},
                       "size": "4 ct / 16 fl oz",
                       "fulfillment": {"inStore": True}}]}

    def test_row_mapping(self):
        r = sr.kroger_product_row(self.DATA, "Monster energy drink")
        self.assertEqual(r["retailer"], "kroger")
        self.assertEqual(r["price_usd"], 6.49)        # promo wins
        self.assertEqual(r["list_price_usd"], 7.99)   # regular kept as list
        self.assertEqual(r["brand"], "Monster")
        self.assertEqual(r["size"], "4 ct / 16 fl oz")
        self.assertEqual(set(r), set(sr.PRODUCT_COLUMNS))

    def test_no_promo(self):
        d = dict(self.DATA, items=[{"price": {"regular": 7.99}, "size": "x"}])
        r = sr.kroger_product_row(d, "t")
        self.assertEqual(r["price_usd"], 7.99)
        self.assertIsNone(r["list_price_usd"])


class TestMerge(unittest.TestCase):
    def _row(self, retailer, iid, title):
        r = {c: "" for c in sr.PRODUCT_COLUMNS}
        r.update({"retailer": retailer, "item_id": iid, "title": title})
        return r

    def test_union_fresh_wins_and_cross_retailer_ids_dont_collide(self):
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "products.csv")
        sr.write_csv(path, sr.PRODUCT_COLUMNS, [
            self._row("target", "1", "Old Target"),
            self._row("costco", "1", "Old Costco"),   # same id, other retailer
        ])
        cols, merged = sr.merge_rows(
            path, sr.PRODUCT_COLUMNS,
            [self._row("target", "1", "Fresh Target"),
             self._row("target", "2", "New Target")],
            sr.product_key)
        self.assertEqual(len(merged), 3)
        by = {(r["retailer"], r["item_id"]): r["title"] for r in merged}
        self.assertEqual(by[("target", "1")], "Fresh Target")
        self.assertEqual(by[("costco", "1")], "Old Costco")
        self.assertEqual(by[("target", "2")], "New Target")

    def test_keyless_rows_survive(self):
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "reviews.csv")
        row = {c: "" for c in sr.REVIEW_COLUMNS}
        sr.write_csv(path, sr.REVIEW_COLUMNS, [dict(row)])
        cols, merged = sr.merge_rows(path, sr.REVIEW_COLUMNS,
                                     [dict(row)], sr.review_key)
        self.assertEqual(len(merged), 2)  # both keyless rows kept

    def test_review_content_fallback_key(self):
        r1 = {"retailer": "target", "review_id": "", "item_id": "1",
              "review_text": "same words", "review_date": "2026-01-01"}
        r2 = dict(r1)
        self.assertEqual(sr.review_key(r1), sr.review_key(r2))
        self.assertIsNotNone(sr.review_key(r1))


class TestHelpers(unittest.TestCase):
    def test_parse_date_formats(self):
        self.assertEqual(sr.parse_date("2026-06-21T14:03:00Z"), "2026-06-21")
        self.assertEqual(sr.parse_date("6/21/2026"), "2026-06-21")
        self.assertEqual(sr.parse_date("June 21, 2026"), "2026-06-21")
        self.assertEqual(sr.parse_date("yesterday"), "yesterday")

    def test_block_marker_error(self):
        self.assertTrue(issubclass(sr.BlockedError, RuntimeError))

    def test_retailer_registry_complete(self):
        self.assertEqual(
            sorted(sr.RETAILERS),
            ["costco", "heb", "kroger", "publix", "target", "traderjoes",
             "wholefoods"])
        for cfg in sr.RETAILERS.values():
            self.assertIn("{q}", cfg["search_url"])
            self.assertTrue(cfg["id_keys"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
