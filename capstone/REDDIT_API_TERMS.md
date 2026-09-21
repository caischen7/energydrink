# Reddit Data API — terms & limits to confirm before the first real run

**Status: NOT VERIFIED. Do not treat this as a terms summary.**

The brief makes a summary of the *current* Reddit Data API terms a precondition
of running the collector. I could not produce one, and I am not going to write
one from memory and present it as current.

## Why not

This session's egress proxy denies outbound CONNECT to external hosts. Every
relevant URL returns nothing:

```
https://www.redditinc.com/policies/data-api-terms        → 000 (connect denied)
https://support.reddithelp.com/hc/.../16160319875092     → 000
https://www.reddit.com/api/v1/access_token               → 000
https://oauth.reddit.com                                 → 000
```

Reddit's API terms and pricing have changed materially more than once
(the 2023 pricing change being the obvious one), and rate limits differ by app
type and by whether use is commercial. A summary written from a model's
training data would be stale in exactly the places that matter, and this is a
compliance gate for academic submission. So it stays blank until someone with
network access fills it in.

## What to confirm, and where

Run these from a machine with normal network access and record the answers
here with the date you read them.

| # | Question | Where |
|---|---|---|
| 1 | Does non-commercial / academic research use qualify for the free tier, and does it need separate registration? | Reddit Data API Terms; the researcher-access page if one still exists |
| 2 | What is the current rate limit for an OAuth **script** app — queries per minute, and over what averaging window? | Reddit API docs / the `x-ratelimit-*` response headers |
| 3 | Is a descriptive `User-Agent` still mandatory, and what format? | Reddit API rules |
| 4 | Are there restrictions on **storing** post/comment text, and for how long? | Data API Terms, "Your Use of the Data" |
| 5 | Are there restrictions on **publishing derived aggregates** in academic work, and is attribution required? | Data API Terms |
| 6 | Does deleted/removed content have to be honoured on re-publication (deletion propagation)? | Data API Terms |
| 7 | Is there a cap on total monthly requests for free-tier use? | Pricing / developer platform docs |

## What the code currently assumes

These are **assumptions in `reddit_collector.py`, not verified facts.** Each is
written where a reviewer can find it. If item 2 above comes back different,
change `QPM_BUDGET` and nothing else needs to move.

| Assumption | Where | If wrong |
|---|---|---|
| Free tier exists for a registered **script** app | module docstring | The collector cannot run at all without a paid arrangement |
| ~100 queries/min is the ceiling; we pace at **60** | `QPM_BUDGET = 60` | Too high → 429s (handled with backoff); too low → slower, harmless |
| A descriptive User-Agent is required | `REDDIT_USER_AGENT` env var, required | Requests refused or throttled harder |
| Aggregates may be published in academic work | the whole output design | Would need permission, or the work reports method only |
| Storing raw text is the risky part, so we don't | `harvest()` yields text and discards it | Already the conservative choice — nothing to undo |

## What is already safe regardless

The collector's design does not depend on the open questions:

- **Official API only.** It calls `oauth.reddit.com` with a bearer token. There
  is no HTML fetch, no `old.reddit.com`, no cookie replay, and no
  unauthenticated fallback anywhere in the file.
- **Credentials from the environment.** Nothing is hardcoded; the token is
  never written to disk or logged.
- **Aggregates only.** `harvest()` yields bare strings, so usernames, ids and
  permalinks cannot reach the analyser or the output even by accident. Raw text
  is scored and discarded.
- **`--dry-run` makes no calls at all**, so the plan can be reviewed before any
  request is issued.

## Decision for Cai

1. Fill in the table above from a networked machine, with the date read.
2. Approve or edit `SEARCH_TERMS` and `SUBREDDITS` in `reddit_collector.py` —
   the brief reserves these for your approval and they are currently proposals.
3. Then, and only then, run without `--dry-run`.
