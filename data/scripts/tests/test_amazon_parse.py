import os
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
#!/usr/bin/env python3
"""Fixture tests for data/scripts/scrape_amazon.py — every parser/transform,
exercised on realistic snippets of Amazon's current (2024-2026) markup.
No network access; runs with plain python3."""

import csv
import importlib.util
import os
import sys
import tempfile
import unittest

SCRIPT = REPO + "/data/scripts/scrape_amazon.py"
spec = importlib.util.spec_from_file_location("scrape_amazon", SCRIPT)
sa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sa)


# --------------------------------------------------------------------------
# Fixtures — trimmed but structurally faithful to live Amazon markup
# --------------------------------------------------------------------------

SEARCH_HTML = """
<div class="s-main-slot s-result-list s-search-results sg-row">
  <!-- ad shell: empty data-asin, must be skipped -->
  <div class="s-result-item AdHolder" data-component-type="s-search-result"
       data-asin="" data-index="1">
    <div class="sg-col-inner"><span>Sponsored shell</span></div>
  </div>

  <!-- full card -->
  <div class="sg-col-4-of-24 s-result-item s-asin"
       data-component-type="s-search-result"
       data-asin="B0C12345XY" data-index="2" data-uuid="aaaa-bbbb">
    <div class="sg-col-inner">
      <span data-component-type="s-product-image">
        <a class="a-link-normal s-no-outline"
           href="/CELSIUS-Sparkling-Orange/dp/B0C12345XY/ref=sr_1_2?keywords=energy+drink&amp;qid=1778700000&amp;sr=8-2">
          <img class="s-image" src="https://m.media-amazon.com/images/I/71x.jpg"
               alt="CELSIUS Sparkling Orange">
        </a>
      </span>
      <div data-cy="title-recipe">
        <a class="a-link-normal s-line-clamp-4 s-link-style a-text-normal"
           href="/CELSIUS-Sparkling-Orange/dp/B0C12345XY/">
          <h2 class="a-size-base-plus a-spacing-none a-color-base a-text-normal">
            <span>CELSIUS Sparkling Orange, Functional Essential Energy Drink
              12 Fl Oz (Pack of 12)</span>
          </h2>
        </a>
      </div>
      <div data-cy="reviews-block">
        <div class="a-row a-size-small">
          <span aria-label="4.7 out of 5 stars">
            <i class="a-icon a-icon-star-small a-star-small-4-5 aok-align-bottom">
              <span class="a-icon-alt">4.7 out of 5 stars</span></i>
          </span>
          <a aria-label="21,467 ratings"
             class="a-link-normal s-underline-text s-underline-link-text s-link-style"
             href="/CELSIUS-Sparkling-Orange/dp/B0C12345XY/#customerReviews">
            <span class="a-size-base s-underline-text">21,467</span>
          </a>
        </div>
      </div>
      <div data-cy="price-recipe">
        <a class="a-link-normal s-no-hover a-text-normal" href="/dp/B0C12345XY/">
          <span class="a-price" data-a-size="xl" data-a-color="base">
            <span class="a-offscreen">$18.99</span>
            <span aria-hidden="true"><span class="a-price-symbol">$</span><span
              class="a-price-whole">18<span class="a-price-decimal">.</span></span><span
              class="a-price-fraction">99</span></span>
          </span>
          <span class="a-price a-text-price" data-a-size="b" data-a-strike="true">
            <span class="a-offscreen">$24.99</span>
            <span aria-hidden="true">$24.99</span>
          </span>
        </a>
      </div>
    </div>
  </div>

  <!-- minimal card: no price block, no reviews yet -->
  <div class="s-result-item s-asin" data-component-type="s-search-result"
       data-asin="B0NEWBRAND1" data-index="3">
    <div class="sg-col-inner">
      <div data-cy="title-recipe">
        <a class="a-link-normal a-text-normal" href="/dp/B0NEWBRAND1/">
          <h2 class="a-size-base-plus a-color-base a-text-normal">
            <span>Nightfall Zero Sugar Energy Drink Variety Pack</span>
          </h2>
        </a>
      </div>
    </div>
  </div>
</div>
"""

DETAIL_HTML = """
<div id="dp" class="grocery en_US">
 <div id="ppd">
  <div id="centerCol">
    <div id="titleSection" class="celwidget">
      <h1 id="title" class="a-size-large a-spacing-none">
        <span id="productTitle" class="a-size-large product-title-word-break">
          CELSIUS Sparkling Orange, Functional Essential Energy Drink 12 Fl Oz
          (Pack of 12)
        </span>
      </h1>
    </div>
    <div id="feature-bullets" class="a-section a-spacing-medium">
      <ul class="a-unordered-list a-vertical a-spacing-mini">
        <li class="a-spacing-mini"><span class="a-list-item">CLIMB HIGHER:
          Elevate your energy with CELSIUS Sparkling Orange</span></li>
        <li class="a-spacing-mini"><span class="a-list-item">ZERO SUGAR: No
          sugar, no aspartame, no artificial colors</span></li>
        <li class="aok-hidden"><span class="a-list-item">internal hidden
          bullet</span></li>
      </ul>
    </div>
  </div>
 </div>
 <div id="wayfinding-breadcrumbs_feature_div" class="celwidget">
   <ul class="a-unordered-list a-horizontal a-size-small">
     <li><span class="a-list-item">
       <a class="a-link-normal a-color-tertiary" href="/grocery/b?node=1">
         Grocery &amp; Gourmet Food</a></span></li>
     <li class="a-breadcrumb-divider"><span class="a-list-item a-color-tertiary">&#8250;</span></li>
     <li><span class="a-list-item">
       <a class="a-link-normal a-color-tertiary" href="/beverages/b?node=2">
         Beverages</a></span></li>
     <li class="a-breadcrumb-divider"><span class="a-list-item a-color-tertiary">&#8250;</span></li>
     <li><span class="a-list-item">
       <a class="a-link-normal a-color-tertiary" href="/energy/b?node=3">
         Energy Drinks</a></span></li>
   </ul>
 </div>
 <div id="productDescription_feature_div">
   <div id="productDescription" class="a-section a-spacing-small">
     <p><span>CELSIUS is functional, Essential Energy — a better-for-you
       premium alternative to traditional energy drinks.</span></p>
   </div>
 </div>
 <div id="reviewsMedley">
  <div id="cm-cr-dp-review-list" class="a-section a-spacing-none reviews-content">

    <div id="R1ABCDEFG12345" data-hook="review" class="a-section review aok-relative">
      <div class="a-row"><a class="a-profile" href="/gp/profile/x">
        <span class="a-profile-name">Jordan T.</span></a></div>
      <div class="a-row">
        <a data-hook="review-title"
           class="a-size-base a-link-normal review-title a-color-base review-title-content a-text-bold"
           href="/gp/customer-reviews/R1ABCDEFG12345/">
          <i data-hook="review-star-rating" class="a-icon a-icon-star a-star-5 review-rating">
            <span class="a-icon-alt">5.0 out of 5 stars</span></i>
          <span class="a-letter-space"></span>
          <span>Best clean energy I have tried</span>
        </a>
      </div>
      <span data-hook="review-date" class="a-size-base a-color-secondary review-date">
        Reviewed in the United States on January 5, 2026</span>
      <div class="a-row a-spacing-small review-data">
        <span data-hook="review-body" class="a-size-base review-text review-text-content">
          <span>Tastes great, no crash at all.<br>Will buy again.</span>
        </span>
      </div>
      <div class="a-row a-spacing-small">
        <span data-hook="avp-badge" class="a-size-mini a-color-state a-text-bold">
          Verified Purchase</span>
      </div>
      <div class="a-row a-spacing-top-small review-comments">
        <span data-hook="helpful-vote-statement" class="a-size-base a-color-tertiary cr-vote-text">
          12 people found this helpful</span>
      </div>
    </div>

    <div id="R2HIJKLMN67890" data-hook="review" class="a-section review aok-relative">
      <div class="a-row">
        <span data-hook="review-title" class="a-size-base review-title a-text-bold">
          <span>Gut, aber teuer</span>
        </span>
        <i data-hook="cmps-review-star-rating" class="a-icon a-icon-star a-star-4 review-rating">
          <span class="a-icon-alt">4.0 out of 5 stars</span></i>
      </div>
      <span data-hook="review-date" class="a-size-base a-color-secondary review-date">
        Reviewed in Germany on June 4, 2021</span>
      <div class="a-row a-spacing-small review-data">
        <span data-hook="review-body" class="a-size-base review-text">
          <span>Schmeckt gut, aber der Preis ist hoch. Read more</span>
        </span>
      </div>
      <div class="a-row">
        <span data-hook="helpful-vote-statement" class="cr-vote-text">
          One person found this helpful</span>
      </div>
    </div>

  </div>
 </div>
</div>
"""

REVIEWS_PAGE_HTML = """
<div id="cm_cr-review_list" class="a-section a-spacing-none reviews-content">
  <div id="R3PAGEDREVIEW1" data-hook="review" class="a-section review aok-relative">
    <div class="a-row">
      <a data-hook="review-title" class="a-link-normal review-title a-text-bold"
         href="/gp/customer-reviews/R3PAGEDREVIEW1/">
        <i data-hook="review-star-rating" class="a-icon a-icon-star a-star-3">
          <span class="a-icon-alt">3.0 out of 5 stars</span></i>
        <span class="a-letter-space"></span>
        <span>Too sweet for me</span>
      </a>
    </div>
    <span data-hook="review-date">Reviewed in the United States on March 14, 2025</span>
    <span data-hook="review-body" class="review-text"><span>Way too sweet,
      gave me jitters.</span></span>
  </div>
  <div id="R4PAGEDREVIEW2" data-hook="review" class="a-section review aok-relative">
    <div class="a-row">
      <a data-hook="review-title" class="a-link-normal review-title a-text-bold"
         href="/gp/customer-reviews/R4PAGEDREVIEW2/">
        <i data-hook="review-star-rating" class="a-icon a-icon-star a-star-5">
          <span class="a-icon-alt">5.0 out of 5 stars</span></i>
        <span class="a-letter-space"></span>
        <span>Great focus drink</span>
      </a>
    </div>
    <span data-hook="review-date">Reviewed in the United States on February 2, 2025</span>
    <span data-hook="review-body" class="review-text"><span>Solid focus, no crash.</span></span>
    <span data-hook="avp-badge">Verified Purchase</span>
  </div>
</div>
"""

CAPTCHA_HTML = """
<html><head><title>Amazon.com</title></head><body>
<form method="get" action="/errors/validateCaptcha" name="">
  <div class="a-box a-color-offset-background">
    <h4>Enter the characters you see below</h4>
    <p class="a-last">Sorry, we just need to make sure you're not a robot.</p>
    <div class="a-row a-text-center">
      <img src="https://images-na.ssl-images-amazon.com/captcha/usvmgloq/Captcha_xyz.jpg">
    </div>
    <input type="text" id="captchacharacters" name="field-keywords"
           class="a-span12" autocapitalize="off" autocorrect="off">
    <button type="submit" class="a-button-text">Continue shopping</button>
  </div>
</form>
</body></html>
"""


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------

class TestSchemas(unittest.TestCase):
    def test_columns_match_committed_headers(self):
        with open(REPO + "/data/amazon/products.csv",
                  encoding="utf-8") as f:
            self.assertEqual(f.readline().strip(),
                             ",".join(sa.PRODUCT_COLUMNS))
        with open(REPO + "/data/amazon/reviews.csv",
                  encoding="utf-8") as f:
            self.assertEqual(f.readline().strip(),
                             ",".join(sa.REVIEW_COLUMNS))


class TestHelpers(unittest.TestCase):
    def test_to_float_int(self):
        self.assertEqual(sa.to_float("$18.99"), 18.99)
        self.assertEqual(sa.to_int("21,467"), 21467)
        self.assertIsNone(sa.to_float(None))
        self.assertIsNone(sa.to_int("no digits"))

    def test_brands(self):
        self.assertEqual(sa.norm_brand("redbull"), "Red Bull")
        self.assertEqual(
            sa.brand_from_title("CELSIUS Sparkling Orange Energy Drink"),
            "Celsius")
        self.assertEqual(
            sa.brand_from_title("Alani Nu Energy Drink Cosmic Stardust"),
            "Alani Nu")
        self.assertIsNone(sa.brand_from_title("Nightfall Zero Sugar"))

    def test_star_rating(self):
        self.assertEqual(sa.parse_star_rating("4.7 out of 5 stars"), 4.7)
        self.assertEqual(sa.parse_star_rating("5.0 out of 5 stars"), 5.0)
        self.assertIsNone(sa.parse_star_rating("Amazon's Choice"))
        self.assertIsNone(sa.parse_star_rating(None))

    def test_helpful_votes(self):
        self.assertEqual(
            sa.parse_helpful_votes("12 people found this helpful"), 12)
        self.assertEqual(
            sa.parse_helpful_votes("One person found this helpful"), 1)
        self.assertEqual(
            sa.parse_helpful_votes("1,204 people found this helpful"), 1204)
        self.assertIsNone(sa.parse_helpful_votes(None))
        self.assertIsNone(sa.parse_helpful_votes(""))

    def test_review_date_line(self):
        country, date = sa.parse_review_date_line(
            "Reviewed in the United States on January 5, 2026")
        self.assertEqual(country, "the United States")  # matches committed CSV
        self.assertEqual(date, "2026-01-05")
        country, date = sa.parse_review_date_line(
            "Reviewed in Germany on June 4, 2021")
        self.assertEqual(country, "Germany")
        self.assertEqual(date, "2021-06-04")
        self.assertEqual(sa.parse_review_date_line("no match"), (None, None))
        # day-first English format some locales use
        self.assertEqual(sa.parse_review_date("4 June 2021"), "2021-06-04")


class TestSearchParse(unittest.TestCase):
    def setUp(self):
        self.products = sa.parse_search_page(SEARCH_HTML)

    def test_skips_empty_asin(self):
        self.assertEqual([p["asin"] for p in self.products],
                         ["B0C12345XY", "B0NEWBRAND1"])

    def test_full_card_fields(self):
        p = self.products[0]
        self.assertTrue(p["title"].startswith("CELSIUS Sparkling Orange"))
        self.assertIn("Pack of 12", p["title"])
        self.assertEqual(p["price_usd"], 18.99)  # not the struck $24.99
        self.assertEqual(p["rating"], 4.7)
        self.assertEqual(p["ratings_total"], 21467)
        self.assertEqual(p["link"], "https://www.amazon.com/dp/B0C12345XY")

    def test_minimal_card_fields(self):
        p = self.products[1]
        self.assertEqual(p["title"],
                         "Nightfall Zero Sugar Energy Drink Variety Pack")
        self.assertIsNone(p["price_usd"])
        self.assertIsNone(p["rating"])
        self.assertIsNone(p["ratings_total"])


class TestDetailParse(unittest.TestCase):
    def setUp(self):
        self.detail = sa.parse_detail_page(DETAIL_HTML)

    def test_title(self):
        self.assertTrue(
            self.detail["title"].startswith("CELSIUS Sparkling Orange"))

    def test_bullets_skip_hidden(self):
        self.assertEqual(len(self.detail["feature_bullets"]), 2)
        self.assertTrue(
            self.detail["feature_bullets"][0].startswith("CLIMB HIGHER"))
        self.assertTrue(
            self.detail["feature_bullets"][1].startswith("ZERO SUGAR"))

    def test_description(self):
        self.assertIn("better-for-you", self.detail["description"])

    def test_categories(self):
        self.assertEqual(self.detail["categories"],
                         ["Grocery & Gourmet Food", "Beverages",
                          "Energy Drinks"])

    def test_on_page_reviews(self):
        r1, r2 = self.detail["reviews"]

        self.assertEqual(r1["review_id"], "R1ABCDEFG12345")
        self.assertEqual(r1["review_title"],
                         "Best clean energy I have tried")
        self.assertEqual(r1["rating"], 5)  # whole-number int, like committed
        self.assertEqual(r1["review_text"],
                         "Tastes great, no crash at all. Will buy again.")
        self.assertEqual(r1["review_date"], "2026-01-05")
        self.assertEqual(r1["review_country"], "the United States")
        self.assertTrue(r1["verified_purchase"])
        self.assertEqual(r1["helpful_votes"], 12)

        self.assertEqual(r2["review_id"], "R2HIJKLMN67890")
        self.assertEqual(r2["review_title"], "Gut, aber teuer")
        self.assertEqual(r2["rating"], 4)  # cmps- hook variant
        self.assertEqual(r2["review_text"],
                         "Schmeckt gut, aber der Preis ist hoch.")  # Read more stripped
        self.assertEqual(r2["review_date"], "2021-06-04")
        self.assertEqual(r2["review_country"], "Germany")
        self.assertFalse(r2["verified_purchase"])
        self.assertEqual(r2["helpful_votes"], 1)


class TestReviewsPage(unittest.TestCase):
    def test_paginated_blocks(self):
        rows = sa.parse_reviews_page(REVIEWS_PAGE_HTML)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["review_id"], "R3PAGEDREVIEW1")
        self.assertEqual(rows[0]["review_title"], "Too sweet for me")
        self.assertEqual(rows[0]["rating"], 3)
        self.assertFalse(rows[0]["verified_purchase"])
        self.assertIsNone(rows[0]["helpful_votes"])
        self.assertEqual(rows[1]["review_id"], "R4PAGEDREVIEW2")
        self.assertTrue(rows[1]["verified_purchase"])
        self.assertEqual(rows[1]["review_date"], "2025-02-02")


class TestCaptchaDetection(unittest.TestCase):
    def test_positive_by_html(self):
        self.assertTrue(sa.looks_captcha(CAPTCHA_HTML))

    def test_positive_by_url(self):
        self.assertTrue(sa.looks_captcha(
            "<html></html>",
            "https://www.amazon.com/errors/validateCaptcha?amzn=x"))

    def test_negative(self):
        self.assertFalse(sa.looks_captcha(SEARCH_HTML,
                                          "https://www.amazon.com/s?k=x"))
        self.assertFalse(sa.looks_captcha(DETAIL_HTML))


class TestRowBuilders(unittest.TestCase):
    def test_product_and_review_rows_have_schema_keys(self):
        card = sa.parse_search_page(SEARCH_HTML)[0]
        prod = sa.product_row(card, "energy drink")
        self.assertEqual(list(prod.keys()), sa.PRODUCT_COLUMNS)
        self.assertEqual(prod["brand"], "Celsius")
        self.assertIsNone(prod["reviews_total"])  # blank, like committed

        detail = sa.parse_detail_page(DETAIL_HTML)
        sa.enrich_product(prod, detail)
        self.assertEqual(prod["categories"],
                         "Grocery & Gourmet Food; Beverages; Energy Drinks")
        self.assertIn(" | ", prod["feature_bullets"])

        rev = sa.review_row(detail["reviews"][0], prod)
        self.assertEqual(list(rev.keys()), sa.REVIEW_COLUMNS)
        self.assertEqual(rev["asin"], "B0C12345XY")
        self.assertEqual(rev["search_term"], "energy drink")


class TestMerge(unittest.TestCase):
    def test_union_prefers_fresh_and_keeps_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "products.csv")
            old_rows = [
                {c: "" for c in sa.PRODUCT_COLUMNS},
                {c: "" for c in sa.PRODUCT_COLUMNS},
            ]
            old_rows[0].update(asin="OLD1", title="Old only product")
            old_rows[1].update(asin="B0C12345XY", title="STALE title",
                               price_usd="9.99")
            sa.write_csv(path, sa.PRODUCT_COLUMNS, old_rows)

            new_rows = [
                {c: None for c in sa.PRODUCT_COLUMNS},
                {c: None for c in sa.PRODUCT_COLUMNS},
            ]
            new_rows[0].update(asin="B0C12345XY", title="FRESH title",
                               price_usd=18.99)
            new_rows[1].update(asin="NEW1", title="Brand new product")

            merged = sa.merge_with_existing(
                path, new_rows, key_column="asin",
                fallback_columns=("link", "title"))
            self.assertEqual([str(r["asin"]) for r in merged],
                             ["OLD1", "B0C12345XY", "NEW1"])
            by_asin = {str(r["asin"]): r for r in merged}
            self.assertEqual(by_asin["B0C12345XY"]["title"], "FRESH title")
            self.assertEqual(by_asin["OLD1"]["title"], "Old only product")

            # round-trip through write_csv keeps the exact header
            sa.write_csv(path, sa.PRODUCT_COLUMNS, merged)
            with open(path, encoding="utf-8") as f:
                self.assertEqual(f.readline().strip(),
                                 ",".join(sa.PRODUCT_COLUMNS))
                self.assertEqual(len(list(csv.DictReader(f, sa.PRODUCT_COLUMNS))), 3)

    def test_missing_file_returns_new_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "reviews.csv")
            new = [{c: "" for c in sa.REVIEW_COLUMNS}]
            new[0].update(review_id="RXYZ", asin="B0")
            merged = sa.merge_with_existing(
                path, new, key_column="review_id",
                fallback_columns=("asin", "review_title", "review_date"))
            self.assertEqual(len(merged), 1)

    def test_blank_key_falls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "reviews.csv")
            a = {c: "" for c in sa.REVIEW_COLUMNS}
            a.update(review_id="", asin="B0", review_title="t1",
                     review_date="2026-01-01")
            b = dict(a, review_title="t2")
            merged = sa.merge_with_existing(
                path, [a, b, dict(a)], key_column="review_id",
                fallback_columns=("asin", "review_title", "review_date"))
            self.assertEqual(len(merged), 2)  # duplicate of `a` collapsed


if __name__ == "__main__":
    unittest.main(verbosity=2)
