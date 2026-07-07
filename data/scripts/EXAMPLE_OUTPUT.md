# Example scraper output

Representative sample rows for every scraper in `data/scripts/`. These are illustrative examples in the **exact column schema each scraper writes** (validated against each script's `*_COLUMNS`); real runs will contain many rows. All scrapers merge incrementally and dedupe on their natural key.

> Generated for reference — not real scraped data. Run the scrapers locally (`python3 data/scripts/run_all.py`) to produce the real CSVs.

| Scraper | Output file(s) | Natural key |
| --- | --- | --- |
| Amazon | `data/amazon/{products,reviews}.csv` | asin / review_id |
| Walmart | `data/walmart/{products,reviews}.csv` | item_id / review_id |
| Retailers | `data/retailers/{products,reviews}.csv` | (retailer, item_id) |
| Kroger | `data/kroger/{products,reviews}.csv` | (retailer, item_id) |
| TikTok | `data/tiktok/{videos,comments}.csv` | video_id / comment_id |
| Facebook | `data/facebook/ads.csv` | ad_id |
| YouTube | `data/youtube/{videos,comments}.csv` | video_id / comment_id |
| Reddit | `raw_data/.../energydrinks_{posts,comments}_*.csv` | id |
| Instagram | `data/instagram/posts.csv` | post shortcode |

## Amazon

`data/scripts/scrape_amazon.py` — Products + on-page reviews from a real browser (no login for the top ~8 reviews per product).

**`data/amazon/products.csv`**

```csv
asin,search_term,title,brand,price_usd,rating,ratings_total,reviews_total,categories,description,feature_bullets,link,scraped_at
B0CH9K1J2L,Celsius energy drink,"CELSIUS Sparkling Orange, Functional Energy Drink, 12 fl oz (Pack of 12)",Celsius,20.34,4.7,18542,,Grocery & Gourmet Food; Beverages; Energy Drinks,"CELSIUS is a functional energy drink with zero sugar, 7 essential vitamins, and no artificial preservatives...","Zero sugar, zero artificial flavors | 200mg caffeine | MetaPlus proprietary blend with green tea | Gluten-free, non-GMO",https://www.amazon.com/dp/B0CH9K1J2L,2026-07-07 09:14:22
```

**`data/amazon/reviews.csv`**

```csv
asin,brand,product_title,search_term,review_id,review_title,review_text,rating,review_date,review_country,verified_purchase,helpful_votes
B0CH9K1J2L,Celsius,"CELSIUS Sparkling Orange, 12 fl oz (Pack of 12)",Celsius energy drink,R1A2B3C4D5E6F7,My daily pre-workout,Clean energy with no jitters and no crash. Orange is the best flavor.,5,2026-06-18,the United States,True,14
```

## Walmart

`data/scripts/scrape_walmart.py` — Products (incl. Walmart's 'N+ bought since yesterday' velocity proxy and bestseller badges) + reviews.

**`data/walmart/products.csv`**

```csv
item_id,search_term,title,brand,price_usd,list_price_usd,rating,reviews_total,seller,sponsored,badges,bought_since_yesterday,availability,link,scraped_at
16935173,energy drink,"Red Bull Energy Drink, 12 fl oz, 12 Pack Cans",Red Bull,18.98,21.48,4.8,8123,Walmart.com,False,Best seller,"1,000+",In stock,https://www.walmart.com/ip/Red-Bull-Energy-Drink/16935173,2026-07-07 09:20:05
```

**`data/walmart/reviews.csv`**

```csv
item_id,brand,product_title,search_term,review_id,review_title,review_text,rating,review_date,verified_purchase,helpful_votes
16935173,Red Bull,"Red Bull Energy Drink, 12 fl oz, 12 Pack Cans",energy drink,gk-88213004,Reliable,Does what it says. Grabbing a 12-pack is cheaper than the gas station.,5,2026-06-29,True,3
```

## Retailers (Target / Trader Joe's / Publix / H-E-B / Costco / Whole Foods)

`data/scripts/scrape_retailers.py` — One CSV pair for all six, with a `retailer` column. Reviews come from Target / Costco / H-E-B.

**`data/retailers/products.csv`**

```csv
retailer,item_id,search_term,title,brand,price_usd,list_price_usd,rating,reviews_total,size,availability,link,scraped_at
target,78025960,energy drink,Celsius Sparkling Fuji Apple Pear Energy Drink - 12pk/12 fl oz Cans,Celsius,18.99,20.49,4.8,2711,12 fl oz/12ct,IN_STOCK,https://www.target.com/p/-/A-78025960,2026-07-07 09:31:10
costco,1628286,Celsius energy drink,"Celsius Live Fit Variety Pack, 12 fl oz, 18-count",Celsius,22.99,,4.6,913,18 ct,,https://www.costco.com/celsius-variety.product.1628286.html,2026-07-07 09:33:41
```

**`data/retailers/reviews.csv`**

```csv
retailer,item_id,brand,product_title,search_term,review_id,review_title,review_text,rating,review_date,verified_purchase,helpful_votes
costco,1628286,Celsius,"Celsius Live Fit Variety Pack, 12 fl oz, 18-count",Celsius energy drink,bv-9931204,Great value at Costco,Cheaper per can than anywhere else and the variety pack has every flavor worth drinking.,5,2026-06-21,True,7
```

## Kroger

`data/scripts/scrape_kroger.py` — kroger.com direct (browser — includes ratings/reviews) or the official free API (products/prices only). `retailer` column = kroger.

**`data/kroger/products.csv`**

```csv
retailer,item_id,search_term,title,brand,price_usd,list_price_usd,rating,reviews_total,size,availability,link,scraped_at
kroger,0001111041660,Monster energy drink,Monster Energy Original Energy Drink,Monster,6.49,7.99,4.7,204,4 ct / 16 fl oz,True,https://www.kroger.com/p/-/0001111041660,2026-07-07 09:41:55
```

**`data/kroger/reviews.csv`**

```csv
retailer,item_id,brand,product_title,search_term,review_id,review_title,review_text,rating,review_date,verified_purchase,helpful_votes
kroger,0001111041660,Monster,Monster Energy Original Energy Drink,Monster energy drink,kr-55120,Classic,The original is still the best. Good price at my local Kroger.,4,2026-05-30,True,2
```

## TikTok

`data/scripts/scrape_tiktok.py` — Brand-account + hashtag videos with engagement stats; optional comments.

**`data/tiktok/videos.csv`**

```csv
video_id,source,author,desc,hashtags,create_date,plays,likes,comments_count,shares,saves,url,brands_mentioned,scraped_at
7389211234567890123,@celsiusofficial,celsiusofficial,New Fuji Apple Pear just dropped 🍏 #celsius #energydrink #livefit,#celsius #energydrink #livefit,2026-06-24,1200000,84000,612,1500,3900,https://www.tiktok.com/@celsiusofficial/video/7389211234567890123,Celsius,2026-07-07 09:50:12
```

**`data/tiktok/comments.csv`**

```csv
video_id,comment_id,author,comment,comment_likes,comment_date,scraped_at
7389211234567890123,7389233445566778899,gymtok_mia,this flavor is unreal 😭 need a case,212,2026-06-24,2026-07-07 09:50:44
```

## Facebook (Meta Ad Library)

`data/scripts/scrape_facebook.py` — Public brand ADS — copy, CTA, platforms, campaign dates. Marketing-intensity signal (no login).

**`data/facebook/ads.csv`**

```csv
ad_id,query,brand,page_name,ad_text,cta,start_date,end_date,active,platforms,snapshot_url,scraped_at
1234567890123456,Celsius,Celsius,CELSIUS Energy Drink,"LIVE FIT. Zero sugar, essential energy. | Grab a variety pack and find your flavor.",Shop Now,2026-06-11,,True,FACEBOOK; INSTAGRAM,https://www.facebook.com/ads/library/?id=1234567890123456,2026-07-07 09:58:30
```

## YouTube

`data/scripts/scrape_youtube.py` — Videos + comments via the official free Data API (or yt-dlp). `transcript` is left blank by design.

**`data/youtube/videos.csv`**

```csv
source,search_query,video_id,title,channel,upload_date,duration_seconds,view_count,like_count,comment_count,description,tags,categories,url,transcript,brands_mentioned
api_v3,best energy drink,dQw4w9WgXcQ,I Tried Every Celsius Flavor - Ranked,EnergyDrinkReviews,2026-05-02,742,410233,18204,1332,Ranking all 14 Celsius flavors from worst to best...,celsius; energy drink; taste test,Howto & Style,https://www.youtube.com/watch?v=dQw4w9WgXcQ,,Celsius
```

**`data/youtube/comments.csv`**

```csv
source,video_id,comment_id,author,comment,comment_likes,comment_date
api_v3,dQw4w9WgXcQ,UgxKREWxIgDrE,@fitwithsam,"The kiwi guava is criminally underrated, glad it ranked high",88,2026-05-03
```

## Reddit

`data/scripts/scrape_reddit.py` — Raw r/EnergyDrinks posts + comments to the untracked raw_data/ dir (no usernames ever). Feeds build_external_datasets.py -> the committed aggregate data/reddit/brand_pulse.csv.

**`raw_data/.../energydrinks_posts_YYYYMMDD.csv`**

```csv
id,title,selftext,created_utc,score,num_comments,permalink
1a2b3c,Celsius vs Alani - which actually tastes better?,"Been switching between them for a month, curious what this sub thinks about flavor and the crash...",1782300000,137,94,/r/EnergyDrinks/comments/1a2b3c/celsius_vs_alani/
```

**`raw_data/.../energydrinks_comments_YYYYMMDD.csv`**

```csv
id,link_id,body,created_utc,score
cx91zz,t3_1a2b3c,"Alani for flavor, Celsius for the actual energy. No contest.",1782301500,42
```

## Instagram

`data/scripts/scrape_instagram.py` — Recent posts from the tracked brand accounts (via instaloader).

**`data/instagram/posts.csv`**

```csv
brand,brand_username,post_url,post_date,likes_count,comments_count,caption,hashtags
Celsius,celsiusofficial,https://www.instagram.com/p/C8xYz1AbcDe/,2026-06-20,24310,512,Summer just got an upgrade 🍊 New Sparkling Fuji Apple Pear is here. #LIVEFIT,#LIVEFIT
```
