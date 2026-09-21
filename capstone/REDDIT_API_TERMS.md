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

## Observed evidence (2026-09-21)

First hard data, read off the live app-creation form at
`https://www.reddit.com/prefs/apps` by Cai and screenshotted. Recorded because
it is verified observation, unlike anything else on this page.

The form states, verbatim:

> By creating an app, you agree to Reddit's **Developer Terms** and **Data Api
> Terms**. **You must also register to use the API.**

and links a **Responsible Builder Policy** at
`https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy`

Three things follow:

1. **Registration is a separate step from creating the app.** "You must also
   register" is not the app form. Question 1 below is therefore answered in
   part — some registration exists and is mandatory — but what it asks for, and
   whether academic use is a category in it, is still unknown.
2. **Three documents bind, not one:** Developer Terms, Data API Terms, and the
   Responsible Builder Policy. The questions below should be checked against
   all three.
3. The Responsible Builder Policy is new relative to anything in this file and
   should be read in full before the first real run.

## What to confirm, and where

Run these from a machine with normal network access and record the answers
here with the date you read them.

| # | Question | Where |
|---|---|---|
| 1 | Does non-commercial / academic research use qualify for the free tier? Registration IS required (observed above) — what does it ask for, and is academic use a category? | The "register to use the API" link on the app form; Data API Terms |
| 2 | What is the current rate limit for an OAuth **script** app — queries per minute, and over what averaging window? | Reddit API docs / the `x-ratelimit-*` response headers |
| 3 | Is a descriptive `User-Agent` still mandatory, and what format? | Reddit API rules |
| 4 | Are there restrictions on **storing** post/comment text, and for how long? | Data API Terms, "Your Use of the Data" |
| 5 | Are there restrictions on **publishing derived aggregates** in academic work, and is attribution required? | Data API Terms |
| 6 | Does deleted/removed content have to be honoured on re-publication (deletion propagation)? | Data API Terms |
| 7 | Is there a cap on total monthly requests for free-tier use? **More load-bearing since deep mode** — 2,100 partitions plus one call per unique post is tens of thousands of requests. | Pricing / developer platform docs |
| 8 | What does the **Responsible Builder Policy** require of a research collector? | The support article linked from the app-creation form |

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
