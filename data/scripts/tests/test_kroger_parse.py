import os
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
"""Offline fixture tests for data/scripts/scrape_kroger.py (no network)."""
import importlib.util
import tempfile
import unittest

SCRIPT = os.path.join(REPO, "data", "scripts", "scrape_kroger.py")
spec = importlib.util.spec_from_file_location("scrape_kroger", SCRIPT)
kr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kr)


class TestBrowserHarvestProducts(unittest.TestCase):
    def test_kroger_search_json(self):
        blob = {"data": {"products": [{
            "productId": "0001111041660",
            "upc": "0001111041660",
            "description": "Monster Energy Original Energy Drink",
            "brand": "Monster",
            "items": [{"price": {"regular": 7.99, "promo": 6.49},
                       "size": "4 ct / 16 fl oz"}],
        }]}}
        rows = kr.harvest_products([blob], "Monster energy drink")
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["retailer"], "kroger")
        self.assertEqual(r["item_id"], "0001111041660")
        self.assertEqual(r["brand"], "Monster")
        self.assertEqual(r["price_usd"], 6.49)       # promo wins
        self.assertEqual(r["list_price_usd"], 7.99)  # regular kept as list
        self.assertEqual(r["size"], "4 ct / 16 fl oz")
        self.assertEqual(set(r), set(kr.PRODUCT_COLUMNS))

    def test_ld_json_with_rating(self):
        blob = {"@type": "Product", "sku": "555",
                "name": "Celsius Sparkling Orange Energy Drink",
                "brand": {"name": "celsius"},
                "offers": {"price": "2.50"},
                "aggregateRating": {"ratingValue": "4.7", "reviewCount": "88"},
                "url": "https://www.kroger.com/p/celsius/555"}
        rows = kr.harvest_products([blob], "Celsius energy drink")
        r = rows[0]
        self.assertEqual(r["item_id"], "555")
        self.assertEqual(r["brand"], "Celsius")
        self.assertEqual(r["rating"], 4.7)
        self.assertEqual(r["reviews_total"], 88)

    def test_junk_without_signal_skipped_and_dedupe(self):
        junk = {"id": "nav-1", "description": "Departments"}
        good = {"productId": "9", "description": "ZOA Energy Drink 12oz",
                "items": [{"price": {"regular": 2.29}}]}
        rows = kr.harvest_products([{"a": [junk, good]}, {"b": good}],
                                   "energy drink")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["brand"], "Zoa")


class TestBrowserHarvestReviews(unittest.TestCase):
    PRODUCT = {"item_id": "9", "brand": "Zoa", "title": "ZOA Energy Drink"}

    def test_bazaarvoice_style(self):
        blob = {"Results": [{"Id": "r1", "Rating": 4,
                             "Title": "Tasty", "ReviewText": "Good stuff, no crash.",
                             "SubmissionTime": "2026-06-01T00:00:00Z",
                             "IsVerifiedPurchaser": True,
                             "TotalPositiveFeedbackCount": 2}]}
        rows = kr.harvest_reviews([blob], self.PRODUCT, "energy drink")
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["review_id"], "r1")
        self.assertEqual(r["rating"], 4.0)
        self.assertEqual(r["review_date"], "2026-06-01")
        self.assertTrue(r["verified_purchase"])
        self.assertEqual(set(r), set(kr.REVIEW_COLUMNS))

    def test_unrated_is_not_a_review(self):
        self.assertEqual(
            kr.harvest_reviews([{"x": {"text": "hi"}}], self.PRODUCT, "t"), [])


class TestApi(unittest.TestCase):
    def test_api_row(self):
        d = {"productId": "p1", "upc": "u1", "description": "Ghost Energy",
             "brand": "Ghost",
             "items": [{"price": {"regular": 2.99, "promo": 2.5},
                        "size": "16 fl oz", "fulfillment": {"inStore": True}}]}
        r = kr.api_product_row(d, "Ghost energy drink")
        self.assertEqual(r["retailer"], "kroger")
        self.assertEqual(r["price_usd"], 2.5)
        self.assertEqual(r["list_price_usd"], 2.99)
        self.assertEqual(r["brand"], "Ghost")
        self.assertIsNone(r["rating"])   # API exposes no reviews/ratings
        self.assertEqual(set(r), set(kr.PRODUCT_COLUMNS))


class TestMerge(unittest.TestCase):
    def test_products_union_fresh_wins(self):
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "products.csv")

        def row(iid, title):
            r = {c: "" for c in kr.PRODUCT_COLUMNS}
            r.update({"retailer": "kroger", "item_id": iid, "title": title})
            return r
        kr.write_csv(path, kr.PRODUCT_COLUMNS, [row("1", "Old"), row("2", "Keep")])
        cols, merged = kr.merge_rows(path, kr.PRODUCT_COLUMNS,
                                     [row("1", "Fresh"), row("3", "New")],
                                     kr.product_key)
        by = {r["item_id"]: r["title"] for r in merged}
        self.assertEqual(by, {"1": "Fresh", "2": "Keep", "3": "New"})


if __name__ == "__main__":
    unittest.main(verbosity=1)
