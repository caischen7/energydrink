import os
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
import json, sys
sys.path.insert(0, REPO + "/data/scripts")
import scrape_walmart as sw

# --- search page fixture ---
item = {
    "__typename": "Product",
    "usItemId": "16935173",
    "name": "Red Bull Energy Drink, 12 fl oz, 12 Pack Cans",
    "brand": "redbull",
    "averageRating": 4.7,
    "numberOfReviews": 8123,
    "sellerName": "Walmart.com",
    "canonicalUrl": "/ip/Red-Bull-Energy-Drink/16935173",
    "priceInfo": {"linePrice": "$18.98", "wasPrice": "$21.48",
                  "currentPrice": {"price": 18.98, "priceString": "$18.98"}},
    "badges": {"flags": [{"text": "Best seller"}]},
    "snackBar": {"text": "1,000+ bought since yesterday"},
    "availabilityStatusDisplayValue": "In stock",
}
html = ('<html><script id="__NEXT_DATA__" type="application/json">'
        + json.dumps({"props": {"pageProps": {"initialData": {"searchResult": {
            "itemStacks": [{"items": [item]}]}}}}})
        + '</script></html>')
data = sw.extract_next_data(html)
found = []
for stack in sw.find_key(data, "itemStacks"):
    for cand in sw.find_key(stack, "items"):
        if isinstance(cand, list):
            found.extend(i for i in cand if isinstance(i, dict))
assert len(found) == 1, found
row = sw.direct_product_row(found[0], "energy drink")
print(json.dumps(row, indent=1))
assert row["brand"] == "Red Bull"
assert row["price_usd"] == 18.98
assert row["list_price_usd"] == 21.48
assert row["reviews_total"] == 8123
assert row["bought_since_yesterday"] == "1,000+"
assert row["badges"] == "Best seller"
assert row["link"].startswith("https://www.walmart.com/ip/")

# --- review fixture ---
review = {
    "reviewId": "abc123",
    "rating": 5,
    "reviewTitle": "Great taste",
    "reviewText": "Love the sugar free version, no crash.",
    "reviewSubmissionTime": "6/28/2026",
    "positiveFeedback": 4,
    "badges": [{"badgeType": "VerifiedPurchaser", "id": "VerifiedPurchaser"}],
}
rrow = sw.direct_review_row(review, row, "energy drink")
print(json.dumps(rrow, indent=1))
assert rrow["review_date"] == "2026-06-28"
assert rrow["verified_purchase"] is True
assert rrow["helpful_votes"] == 4

# --- serpapi fixtures ---
sp = sw.serpapi_product_row({
    "us_item_id": "555", "title": "CELSIUS Sparkling Orange, 12 Pack",
    "rating": 4.8, "reviews": 900, "seller_name": "Walmart.com",
    "primary_offer": {"offer_price": 17.48},
    "product_page_url": "https://www.walmart.com/ip/x/555"}, "Celsius energy drink")
assert sp["brand"] == "Celsius" and sp["price_usd"] == 17.48
sr = sw.serpapi_review_row({
    "review_id": "z9", "title": "ok", "text": "fine", "rating": 3,
    "review_submission_time": "July 1, 2026", "positive_feedback": 1,
    "verified_purchase": True}, sp, "Celsius energy drink")
assert sr["review_date"] == "2026-07-01"

# date fallback keeps raw string
assert sw.parse_review_date("about a month ago") == "about a month ago"
# block detection
try:
    sw.extract_next_data("<html>Robot or human? px-captcha</html>")
    raise AssertionError("should have raised BlockedError")
except sw.BlockedError:
    pass
print("ALL PARSE TESTS PASSED")

# --- multi-blob review dedupe (SSR + captured GraphQL) ---
ssr_blob = {"props": {"initialData": {"data": {"reviews": {
    "customerReviews": [dict(review)]}}}}}
gql_blob = {"data": {"reviews": {"customerReviews": [
    dict(review),  # duplicate of the SSR one
    {"reviewId": "xyz789", "rating": 4, "reviewTitle": "Solid",
     "reviewText": "Good flavor", "reviewSubmissionTime": "July 2, 2026",
     "positiveFeedback": 0},
]}}}
out = sw.direct_reviews("16935173", 1, 0, fetch_blobs=lambda url: [ssr_blob, gql_blob])
assert [r["reviewId"] for r in out] == ["abc123", "xyz789"], out
print("MULTI-BLOB DEDUPE TEST PASSED")

# --- merge_rows: old CSV on disk + overlapping new rows -> union, new wins ---
import csv, os, tempfile
tmpdir = tempfile.mkdtemp()
ppath = os.path.join(tmpdir, "products.csv")

def prod(item_id, title, price):
    r = {c: "" for c in sw.PRODUCT_COLUMNS}
    r.update({"item_id": item_id, "title": title, "price_usd": price})
    return r

# seed the "disk" file with two old rows (item_id 1 and 2)
sw.write_csv(ppath, sw.PRODUCT_COLUMNS,
             [prod("1", "Old One", "9.99"), prod("2", "Old Two", "10.99")])
# fresh scrape: item_id 2 (updated) + item_id 3 (new); 2 is an int on purpose
# to prove key comparison is str-normalized against disk strings
new_rows = [prod(2, "Fresh Two", 12.48), prod("3", "Fresh Three", 8.99)]
cols, merged = sw.merge_rows(ppath, sw.PRODUCT_COLUMNS, new_rows, "item_id")
assert cols == sw.PRODUCT_COLUMNS, cols  # file column order preserved
by_id = {str(r["item_id"]): r for r in merged}
assert set(by_id) == {"1", "2", "3"}, sorted(by_id)
assert by_id["1"]["title"] == "Old One"          # old-only row kept
assert by_id["2"]["title"] == "Fresh Two"        # fresh row wins on collision
assert by_id["3"]["title"] == "Fresh Three"      # new row appended
assert len(merged) == 3, merged
print("MERGE UNION TEST PASSED")

# rows lacking the key get synthetic keys and are never silently dropped
sw.write_csv(ppath, sw.PRODUCT_COLUMNS, [prod("", "Old Keyless", "1.00")])
cols, merged = sw.merge_rows(
    ppath, sw.PRODUCT_COLUMNS,
    [prod(None, "New Keyless A", "2.00"), prod(None, "New Keyless B", "3.00")],
    "item_id")
assert len(merged) == 3, merged  # 1 old + 2 new keyless rows all survive
assert [r["title"] for r in merged] == ["Old Keyless", "New Keyless A",
                                        "New Keyless B"], merged
print("MERGE SYNTHETIC-KEY TEST PASSED")

# column order of a pre-existing (legacy) file is preserved
lpath = os.path.join(tmpdir, "legacy.csv")
with open(lpath, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["title", "item_id"])
    w.writeheader()
    w.writerow({"title": "Legacy", "item_id": "7"})
cols, merged = sw.merge_rows(lpath, sw.PRODUCT_COLUMNS,
                             [prod("8", "Fresh Eight", "5.00")], "item_id")
assert cols == ["title", "item_id"], cols
assert len(merged) == 2
print("MERGE COLUMN-ORDER TEST PASSED")

# no file on disk -> merge is a no-op passthrough
mpath = os.path.join(tmpdir, "missing.csv")
cols, merged = sw.merge_rows(mpath, sw.PRODUCT_COLUMNS,
                             [prod("9", "Nine", "4.00")], "item_id")
assert cols == sw.PRODUCT_COLUMNS and len(merged) == 1

# --fresh semantics: skip merge_rows entirely, write_csv overwrites the file
sw.write_csv(ppath, sw.PRODUCT_COLUMNS,
             [prod("1", "Old One", "9.99"), prod("2", "Old Two", "10.99")])
sw.write_csv(ppath, sw.PRODUCT_COLUMNS, [prod("3", "Only Three", "8.99")])
fresh_rows, fresh_cols = sw.read_csv_rows(ppath)
assert fresh_cols == sw.PRODUCT_COLUMNS
assert [r["item_id"] for r in fresh_rows] == ["3"], fresh_rows
print("FRESH OVERWRITE TEST PASSED")

# --- review_key: disk rows (all-str) match freshly scraped rows ---
rvpath = os.path.join(tmpdir, "reviews.csv")
sw.write_csv(rvpath, sw.REVIEW_COLUMNS, [rrow])          # rrow from earlier
disk_reviews, _ = sw.read_csv_rows(rvpath)
assert sw.review_key(disk_reviews[0]) == sw.review_key(rrow)
# id-less rows fall back to the (item_id, text, date) content tuple
idless_fresh = {"review_id": None, "item_id": "16935173",
                "review_text": "no id here", "review_date": "2026-01-05"}
idless_disk = {"review_id": "", "item_id": "16935173",
               "review_text": "no id here", "review_date": "2026-01-05"}
k = sw.review_key(idless_fresh)
assert isinstance(k, tuple) and k == sw.review_key(idless_disk)
assert isinstance(sw.review_key(rrow), str)  # id-bearing rows keep str keys

# seeding the in-run set from disk skips already-collected reviews
review_ids = set()
for old in disk_reviews:
    review_ids.add(sw.review_key(old))
assert sw.review_key(rrow) in review_ids          # re-scraped dup is skipped
fresh_new = dict(rrow, review_id="brand-new-42")
assert sw.review_key(fresh_new) not in review_ids  # genuinely new one is not
print("REVIEW SEED/KEY TESTS PASSED")

# reviews merge: overlap on review_id, fresh wins, id-less old row survives
old_r = dict(rrow, review_title="stale title")
sw.write_csv(rvpath, sw.REVIEW_COLUMNS, [old_r, idless_disk])
cols, merged = sw.merge_rows(rvpath, sw.REVIEW_COLUMNS,
                             [dict(rrow), dict(fresh_new)], "review_id")
assert cols == sw.REVIEW_COLUMNS
assert len(merged) == 3, merged  # abc123 (fresh), idless, brand-new-42
by_key = {sw.review_key(r): r for r in merged}
assert by_key["abc123"]["review_title"] == "Great taste"  # fresh beat stale
assert "brand-new-42" in by_key
print("REVIEW MERGE TEST PASSED")

import shutil
shutil.rmtree(tmpdir)
print("ALL MERGE TESTS PASSED")
