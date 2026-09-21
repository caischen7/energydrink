#!/usr/bin/env python3
# ===========================================================================
#  GENERATED FILE - DO NOT EDIT BY HAND
#
#  Standalone bundle of the Bogus Banana capstone Reddit collector.
#  Everything needed is embedded; stdlib only; no repo, no pip install.
#
#      python reddit_deep_standalone.py --self-test    # no creds, no network
#      python reddit_deep_standalone.py --dry-run      # show the plan
#      python reddit_deep_standalone.py                # deep pull, bounded
#
#  Credentials: put a .env next to this file, or export the three variables.
#      REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET / REDDIT_USER_AGENT
#  Get them from a **script** app at https://www.reddit.com/prefs/apps
#
#  Built 2026-09-21 22:00 UTC from 5c054e7
#  Source of truth: capstone/collectors/ in the repo. Edit there, then rerun
#  capstone/scripts/build_standalone.py - edits made here are lost on rebuild.
# ===========================================================================
import base64 as _b64, sys as _sys, types as _types

_EMBEDDED = {
    "classify_target_consumers": (
        "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiIKTGFiZWwgZXZlcnkgUERJIGVuZXJneS1kcmluayBT"
        "S1Ugd2l0aCB0aGUgY29uc3VtZXIgaXQgaXMgYnVpbHQgZm9yLgoKUmVhZHMgIGRhdGEvYnEvcGRp"
        "X3VuaXF1ZV9wcm9kdWN0cy5jc3YgICgyLDMwOSBHVElOcyBwdWxsZWQgZnJvbSBwZGlfZGFpbHlf"
        "YWdnKQpXcml0ZXMgdGhlIHNhbWUgZmlsZSBiYWNrIHdpdGggZm91ciBhZGRlZCBjb2x1bW5zIGRl"
        "c2NyaWJpbmcgd2hvIGJ1eXMgaXQ6CgogICAgdGFyZ2V0X2NvbnN1bWVyICAgdGhlIGF1ZGllbmNl"
        "IGluIHBsYWluIHdvcmRzIOKAlCAiR3ltICYgZml0bmVzcyIsCiAgICAgICAgICAgICAgICAgICAg"
        "ICAiV29tZW4gMTgtMzQiLCAiU2hpZnQgd29ya2VycyAmIG1pbGl0YXJ5IiwgLi4uCiAgICB0YXJn"
        "ZXRfYWdlICAgICAgICB0aGUgYWdlIGJhbmQgdGhhdCBvdmVyLWluZGV4ZXMKICAgIHRhcmdldF9n"
        "ZW5kZXIgICAgIE1hbGUtc2tld2luZyAvIEZlbWFsZS1za2V3aW5nIC8gTWl4ZWQKICAgIHRhcmdl"
        "dF9ub3RlcyAgICAgIG9uZSBsaW5lIG9uIHdoYXQgdGhhdCBidXllciB3YW50cwoKQWdlcyBhbmQg"
        "Z2VuZGVyIGNvbWUgZnJvbSBNUkktU2ltbW9ucyAyMDI0IHdoZXJlIHRoZSBicmFuZCB3YXMgbWVh"
        "c3VyZWQKKFJlZCBCdWxsLCBNb25zdGVyLCBSb2Nrc3RhciwgTk9TLCBCYW5nLCBBTVAsIDUtaG91"
        "ciBFbmVyZ3kpOyBmcm9tIHRoZSBicmFuZCdzCnB1Ymxpc2hlZCBwb3NpdGlvbmluZyBlbHNld2hl"
        "cmU7IGFuZCBmcm9tIHByb2R1Y3QgYXR0cmlidXRlcyBmb3IgdGhlIGxvbmcgdGFpbApvZiBzbWFs"
        "bCBicmFuZHMuCgpCcmFuZCBydWxlcyB3aW4gb3ZlciBhdHRyaWJ1dGUgcnVsZXMsIGJlY2F1c2Ug"
        "YSBicmFuZCdzIHBvc2l0aW9uaW5nIGlzIGEgc3Ryb25nZXIKc2lnbmFsIHRoYW4gYSBjYW4gc2l6"
        "ZS4gQXR0cmlidXRlIHJ1bGVzIHRoZW4gY2F0Y2ggdGhlIGxvbmcgdGFpbCBvZiAyMDAtb2RkCmJy"
        "YW5kcyBub2JvZHkgaGFzIHByb2ZpbGVkLCBhbmQgc3BsaXQgdGhlIGJpZyBicmFuZHMnIHplcm8t"
        "c3VnYXIgbGluZXMgb3V0IG9mCnRoZWlyIHN1Z2FyZWQgcGFyZW50cyDigJQgdGhvc2UgZ2VudWlu"
        "ZWx5IHNlbGwgdG8gZGlmZmVyZW50IHBlb3BsZS4KClJlcnVubmFibGU6IGl0IHN0cmlwcyBpdHMg"
        "b3duIGNvbHVtbnMgZmlyc3QsIHNvIGl0IG5ldmVyIGRvdWJsZS1hcHBlbmRzLgoiIiIKaW1wb3J0"
        "IGNzdgppbXBvcnQgb3MKaW1wb3J0IHJlCmltcG9ydCBzeXMKClNSQyA9IG9zLnBhdGguam9pbihv"
        "cy5wYXRoLmRpcm5hbWUoX19maWxlX18pLCAiLi4iLCAiYnEiLCAicGRpX3VuaXF1ZV9wcm9kdWN0"
        "cy5jc3YiKQoKQURERUQgPSBbInRhcmdldF9jb25zdW1lciIsICJ0YXJnZXRfYWdlIiwgInRhcmdl"
        "dF9nZW5kZXIiLCAidGFyZ2V0X25vdGVzIiwKICAgICAgICAgImZsYXZvcl9mYW1pbHkiXQoKIyAt"
        "LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tIGF1ZGllbmNl"
        "IC0+IGFnZS9nZW5kZXIvbm90ZQojIEFnZSBiYW5kcyBmb3IgdGhlIFNpbW1vbnMtbWVhc3VyZWQg"
        "YnJhbmRzIGFyZSB0aGUgb25lcyB0aGF0IGFjdHVhbGx5CiMgb3Zlci1pbmRleCBpbiBNUkktU2lt"
        "bW9ucyAyMDI0IChpbmRleCA+MTUwIHZzIGFsbCBVUyBhZHVsdHMpLgpBVURJRU5DRSA9IHsKICAg"
        "ICJZb3VuZyBhZHVsdHMiOiAoCiAgICAgICAgIjE4LTM0IiwgIk1hbGUtc2tld2luZyIsCiAgICAg"
        "ICAgIkRyaW5rcyBpdCBvdXQgb2YgaGFiaXQgYW5kIGJyYW5kIGxveWFsdHkuIDI1LTM0cyBhcmUg"
        "YWJvdXQgdHdpY2UgYXMgIgogICAgICAgICJsaWtlbHkgYXMgdGhlIGF2ZXJhZ2UgYWR1bHQgdG8g"
        "ZHJpbmsgUmVkIEJ1bGwsIGFuZCAxLjh4IGZvciBNb25zdGVyLiIpLAogICAgIkNhbG9yaWUtY3V0"
        "dGVycyI6ICgKICAgICAgICAiMjUtNDQiLCAiTWl4ZWQiLAogICAgICAgICJUaGUgc2FtZSBtYWlu"
        "c3RyZWFtIGRyaW5rZXIgY3V0dGluZyBzdWdhciwgbm90IGNoYXNpbmcgZml0bmVzcy4gIgogICAg"
        "ICAgICJUaGUgemVyby1zdWdhciBsaW5lcyByZWFjaCBvbGRlciBhbmQgbW9yZSBmZW1hbGUgYnV5"
        "ZXJzIHRoYW4gdGhlIHN1Z2FyZWQgb25lcy4iKSwKICAgICJHeW0gJiBmaXRuZXNzIjogKAogICAg"
        "ICAgICIyNC0zNSIsICJNYWxlLXNrZXdpbmcgKH43MC8zMCkiLAogICAgICAgICJXYW50cyBhIHBy"
        "ZS13b3Jrb3V0IHRoZXkgY2FuIGRyaW5rIGZyb20gYSBjYW4uIEJ1eXMgb24gY2FmZmVpbmUgZG9z"
        "ZSwgIgogICAgICAgICJhbWlub3MgYW5kIHplcm8gc3VnYXIuIFJvdWdobHkgNyBpbiAxMCBhcmUg"
        "bWVuLiIpLAogICAgIldvbWVuIChmaXRuZXNzICYgd2VsbG5lc3MpIjogKAogICAgICAgICIxOC0z"
        "NCIsICJGZW1hbGUtc2tld2luZyIsCiAgICAgICAgIk1pbGxlbm5pYWwgYW5kIEdlbiBaIHdvbWVu"
        "IHdpdGggZml0bmVzcyBhbmQgd2VsbG5lc3MgZ29hbHMuIFNsaW0gY2FucywgIgogICAgICAgICJm"
        "cnVpdCBmbGF2b3JzLCB3ZWxsbmVzcyBsYW5ndWFnZSBpbnN0ZWFkIG9mIGV4dHJlbWUtc3BvcnRz"
        "IGxhbmd1YWdlLiIpLAogICAgIkdhbWVycyAmIGNyZWF0b3JzIjogKAogICAgICAgICIxNi0yNyIs"
        "ICJNYWxlLXNrZXdpbmciLAogICAgICAgICJCdXlzIHRoZSBpbmZsdWVuY2VyIGFuZCB0aGUgZmxh"
        "dm91ciBkcm9wIGFzIG11Y2ggYXMgdGhlIGNhZmZlaW5lLiAiCiAgICAgICAgIk1vc3RseSByZWFj"
        "aGVkIG9ubGluZSwgc28gY29udmVuaWVuY2Ugc3RvcmVzIHVuZGVyc3RhdGUgdGhpcyBncm91cC4i"
        "KSwKICAgICJTaGlmdCB3b3JrZXJzICYgbWlsaXRhcnkiOiAoCiAgICAgICAgIjI1LTQ0IiwgIk1h"
        "bGUtc2tld2luZyIsCiAgICAgICAgIlByaWNlIHBlciBvdW5jZSBkZWNpZGVzIGl0LiBEcml2ZXJz"
        "LCB0cmFkZXMgYW5kIGRlcGxveWVkIHBlcnNvbm5lbCAiCiAgICAgICAgImJ1eWluZyB0aGUgY2hl"
        "YXBlc3QgZWZmZWN0aXZlIGNhbiBvbiB0aGUgc2hlbGYuIiksCiAgICAiSGVhbHRoLWNvbnNjaW91"
        "cyBhZHVsdHMiOiAoCiAgICAgICAgIjMwLTU1IiwgIk1peGVkIiwKICAgICAgICAiUmVqZWN0cyB0"
        "aGUgc3RpbXVsYW50IGZyYW1pbmcgZW50aXJlbHkuIFdhbnRzIG9yZ2FuaWMsIHllcmJhIG1hdGUg"
        "b3IgIgogICAgICAgICJwbGFudCBjYWZmZWluZSwgYW5kIHNrZXdzIG9sZGVyIGFuZCBiZXR0ZXIt"
        "b2ZmIHRoYW4gdGhlIGNhdGVnb3J5LiIpLAogICAgIkNvZmZlZSBkcmlua2VycyI6ICgKICAgICAg"
        "ICAiMzAtNTUiLCAiTWl4ZWQiLAogICAgICAgICJXYW50cyB0aGUgY2FmZmVpbmUgd2l0aG91dCBp"
        "ZGVudGlmeWluZyBhcyBhbiBlbmVyZ3ktZHJpbmsgZHJpbmtlci4gIgogICAgICAgICJDb21lcyBp"
        "biB0aHJvdWdoIGNvbGQgYnJldyBhbmQgY2FubmVkIGNvZmZlZSByYXRoZXIgdGhhbiB0aGUgZW5l"
        "cmd5IGFpc2xlLiIpLAogICAgIk9sZGVyIGZ1bmN0aW9uYWwgdXNlcnMiOiAoCiAgICAgICAgIjM1"
        "LTU0IiwgIk1hbGUtc2tld2luZyIsCiAgICAgICAgIlRha2VzIGl0IGFzIGEgZG9zZSwgbm90IGEg"
        "ZHJpbmsuIEhlYXZpbHkgc2tld2VkIHRvd2FyZCBhdmlkIHNwb3J0cyAiCiAgICAgICAgImZhbnMs"
        "IHdobyBhcmUgbW9yZSB0aGFuIHR3aWNlIGFzIGxpa2VseSBhcyBhdmVyYWdlIHRvIGJ1eSBpdC4i"
        "KSwKfQoKIyBXaGVyZSBhIGJyYW5kJ3Mgb3duIG1lYXN1cmVkIGF1ZGllbmNlIGRpZmZlcnMgZnJv"
        "bSBpdHMgZ3JvdXAsIHNheSBzbyBvbiB0aGUKIyByb3cgaXRzZWxmIHJhdGhlciB0aGFuIG1ha2lu"
        "ZyB0aGUgcmVhZGVyIGluZmVyIGl0IGZyb20gdGhlIGdyb3VwIG5vdGUuCkJSQU5EX05PVEUgPSB7"
        "CiAgICAiUm9ja3N0YXIiOgogICAgICAgICJSZWFkcyBhcyBhIHlvdW5nIGJyYW5kIGJ1dCBpdHMg"
        "ZHJpbmtlcnMgYXJlIGNvbmNlbnRyYXRlZCBpbiB0aGUgMzUtNDQgIgogICAgICAgICJiYW5kLCB3"
        "aG8gYXJlIGFib3V0IDEuOHggbW9yZSBsaWtlbHkgdGhhbiBhdmVyYWdlIHRvIGRyaW5rIGl0LiIs"
        "CiAgICAiTk9TIjoKICAgICAgICAiU2tld3MgZGlzdGluY3RseSBtYWxlIC0gYWJvdXQgdGhyZWUg"
        "cXVhcnRlcnMgb2YgZHJpbmtlcnMgYXJlIGluICIKICAgICAgICAibWFsZS1oZWFkZWQgaG91c2Vo"
        "b2xkcyAtIGFuZCBjb25jZW50cmF0ZXMgaW4gdGhlIDI1LTM0IGJhbmQuIiwKICAgICJCYW5nIjoK"
        "ICAgICAgICAiVGhlIHlvdW5nZXN0IGF1ZGllbmNlIG1lYXN1cmVkIGluIHRoZSBjYXRlZ29yeTog"
        "MTgtMjRzIGFyZSBuZWFybHkgIgogICAgICAgICJ0d2ljZSBhcyBsaWtlbHkgYXMgdGhlIGF2ZXJh"
        "Z2UgYWR1bHQgdG8gZHJpbmsgaXQuIiwKICAgICI1LUhvdXIgRW5lcmd5IjoKICAgICAgICAiVGFr"
        "ZW4gYXMgYSBkb3NlLCBub3QgYSBkcmluay4gQXZpZCBzcG9ydHMgZmFucyBhcmUgb3ZlciB0d2lj"
        "ZSBhcyAiCiAgICAgICAgImxpa2VseSBhcyBhdmVyYWdlIHRvIGJ1eSBpdCwgYW5kIEJsYWNrL0Fm"
        "cmljYW4gQW1lcmljYW4gYWR1bHRzIDEuNzV4LiIsCiAgICAiUmVkIEJ1bGwiOgogICAgICAgICIy"
        "NS0zNHMgYXJlIGFib3V0IHR3aWNlIGFzIGxpa2VseSBhcyB0aGUgYXZlcmFnZSBhZHVsdCB0byBk"
        "cmluayBpdCAtICIKICAgICAgICAidGhlIHlvdW5nZXN0LXNrZXdpbmcgbGFyZ2UgYnJhbmQgaW4g"
        "dGhlIGNhdGVnb3J5LiIsCiAgICAiTW9uc3RlciI6CiAgICAgICAgIjI1LTM0cyBhcmUgYWJvdXQg"
        "MS44eCBhcyBsaWtlbHkgYXMgYXZlcmFnZSB0byBkcmluayBpdCwgd2l0aCBhICIKICAgICAgICAi"
        "bm90aWNlYWJsZSBza2V3IHRvd2FyZCBsb3dlci1pbmNvbWUgaG91c2Vob2xkcy4iLAogICAgIkNl"
        "bHNpdXMiOgogICAgICAgICJSZWFkIGFzIGEgd29tZW4ncyBicmFuZCwgYnV0IGNvbnN1bXB0aW9u"
        "IGlzIGNsb3NlIHRvIGFuIGV2ZW4gNTAvNTAgIgogICAgICAgICJzcGxpdCBiZXR3ZWVuIG1lbiBh"
        "bmQgd29tZW4uIiwKICAgICJBbGFuaSBOdSI6CiAgICAgICAgIkJ1aWx0IHNwZWNpZmljYWxseSBm"
        "b3IgTWlsbGVubmlhbCBhbmQgR2VuIFogd29tZW4sIGFuZCB0aGUgYXVkaWVuY2UgIgogICAgICAg"
        "ICJtYXRjaGVzIHRoZSBpbnRlbnQgbW9yZSBjbG9zZWx5IHRoYW4gYW55IG90aGVyIGJyYW5kIGhl"
        "cmUuIiwKfQoKIyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0gYnJhbmQgLT4gYXVkaWVuY2UKQlJBTkQgPSB7CiAgICAjIC0tLSBhdWRpZW5jZSBt"
        "ZWFzdXJlZCBkaXJlY3RseSBpbiBNUkktU2ltbW9ucyAyMDI0IC0tLQogICAgIlJlZCBCdWxsIjog"
        "IllvdW5nIGFkdWx0cyIsCiAgICAiTW9uc3RlciI6ICJZb3VuZyBhZHVsdHMiLAogICAgIlJvY2tz"
        "dGFyIjogIllvdW5nIGFkdWx0cyIsICAgICAgICAgICMgbm90ZTogc2tld3MgMzUtNDQsIG5vdCB5"
        "b3VuZzsgc2VlIEFHRV9PVkVSUklERQogICAgIk5PUyI6ICJTaGlmdCB3b3JrZXJzICYgbWlsaXRh"
        "cnkiLAogICAgIkJhbmciOiAiR3ltICYgZml0bmVzcyIsCiAgICAiQU1QIjogIllvdW5nIGFkdWx0"
        "cyIsCiAgICAiTXRuIERldyBBTVAiOiAiWW91bmcgYWR1bHRzIiwKICAgICI1LUhvdXIgRW5lcmd5"
        "IjogIk9sZGVyIGZ1bmN0aW9uYWwgdXNlcnMiLAogICAgIyAtLS0gYXVkaWVuY2UgZnJvbSB0aGUg"
        "YnJhbmQncyBwdWJsaXNoZWQgcG9zaXRpb25pbmcgLS0tCiAgICAiQ2Vsc2l1cyI6ICJXb21lbiAo"
        "Zml0bmVzcyAmIHdlbGxuZXNzKSIsCiAgICAiQWxhbmkgTnUiOiAiV29tZW4gKGZpdG5lc3MgJiB3"
        "ZWxsbmVzcykiLAogICAgIkJsb29tIjogIldvbWVuIChmaXRuZXNzICYgd2VsbG5lc3MpIiwKICAg"
        "ICJDNCI6ICJHeW0gJiBmaXRuZXNzIiwKICAgICJHaG9zdCI6ICJHeW0gJiBmaXRuZXNzIiwKICAg"
        "ICJSeXNlIjogIkd5bSAmIGZpdG5lc3MiLAogICAgIlJFRENPTjEiOiAiR3ltICYgZml0bmVzcyIs"
        "CiAgICAiQnVja2VkIFVwIjogIkd5bSAmIGZpdG5lc3MiLAogICAgIkNlbGx1Y29yIjogIkd5bSAm"
        "IGZpdG5lc3MiLAogICAgIjFzdCBQaG9ybSI6ICJHeW0gJiBmaXRuZXNzIiwKICAgICJPcHRpbXVt"
        "IE51dHJpdGlvbiI6ICJHeW0gJiBmaXRuZXNzIiwKICAgICJYeWllbmNlIjogIkd5bSAmIGZpdG5l"
        "c3MiLAogICAgIkFkcmVuYWxpbmUgU2hvYyI6ICJHeW0gJiBmaXRuZXNzIiwKICAgICIzRCBFbmVy"
        "Z3kiOiAiR3ltICYgZml0bmVzcyIsCiAgICAiR29yaWxsYSI6ICJHeW0gJiBmaXRuZXNzIiwKICAg"
        "ICJSZWlnbiI6ICJHeW0gJiBmaXRuZXNzIiwKICAgICJHYXRvcmFkZSBGYXN0IFR3aXRjaCI6ICJH"
        "eW0gJiBmaXRuZXNzIiwKICAgICJaT0EiOiAiR3ltICYgZml0bmVzcyIsCiAgICAiRyBGVUVMIjog"
        "IkdhbWVycyAmIGNyZWF0b3JzIiwKICAgICJQcmltZSI6ICJHYW1lcnMgJiBjcmVhdG9ycyIsCiAg"
        "ICAiRy5PLkEuVC4gRnVlbCI6ICJHYW1lcnMgJiBjcmVhdG9ycyIsCiAgICAiUmlwIEl0IjogIlNo"
        "aWZ0IHdvcmtlcnMgJiBtaWxpdGFyeSIsCiAgICAiVmVub20iOiAiU2hpZnQgd29ya2VycyAmIG1p"
        "bGl0YXJ5IiwKICAgICJGdWxsIFRocm90dGxlIjogIlNoaWZ0IHdvcmtlcnMgJiBtaWxpdGFyeSIs"
        "CiAgICAiUmFwdG9yIjogIlNoaWZ0IHdvcmtlcnMgJiBtaWxpdGFyeSIsCiAgICAiTGlxdWlkIElj"
        "ZSI6ICJTaGlmdCB3b3JrZXJzICYgbWlsaXRhcnkiLAogICAgIk9sJyBHbG9yeSI6ICJTaGlmdCB3"
        "b3JrZXJzICYgbWlsaXRhcnkiLAogICAgIkJ1bSBFbmVyZ3kiOiAiU2hpZnQgd29ya2VycyAmIG1p"
        "bGl0YXJ5IiwKICAgICJBZHJlbmFsaW5lIFJ1c2giOiAiU2hpZnQgd29ya2VycyAmIG1pbGl0YXJ5"
        "IiwKICAgICJBcml6b25hIEVuZXJneSI6ICJTaGlmdCB3b3JrZXJzICYgbWlsaXRhcnkiLAogICAg"
        "Ikd1YXlha2kiOiAiSGVhbHRoLWNvbnNjaW91cyBhZHVsdHMiLAogICAgIllhY2hhayI6ICJIZWFs"
        "dGgtY29uc2Npb3VzIGFkdWx0cyIsCiAgICAiTXRuIERldyBSaXNlIjogIkhlYWx0aC1jb25zY2lv"
        "dXMgYWR1bHRzIiwKICAgICJVcHRpbWUiOiAiSGVhbHRoLWNvbnNjaW91cyBhZHVsdHMiLAogICAg"
        "IlN0YXJidWNrcyBCYXlhIjogIkhlYWx0aC1jb25zY2lvdXMgYWR1bHRzIiwKICAgICJCbHVlIEJv"
        "dHRsZSBDb2ZmZWUiOiAiQ29mZmVlIGRyaW5rZXJzIiwKICAgICJCbGFjayBSaWZsZSBDb2ZmZWUg"
        "Q29tcGFueSI6ICJDb2ZmZWUgZHJpbmtlcnMiLAogICAgIk10biBEZXcgKGVuZXJneSkiOiAiWW91"
        "bmcgYWR1bHRzIiwKfQoKIyBXaGVyZSBTaW1tb25zIGNvbnRyYWRpY3RzIHRoZSBhdWRpZW5jZSdz"
        "IGRlZmF1bHQgYWdlIGJhbmQsIHRoZSBtZWFzdXJlZAojIG51bWJlciB3aW5zIOKAlCBSb2Nrc3Rh"
        "ciByZWFkcyBhcyBhIHlvdW5nIGJyYW5kIGJ1dCBpbmRleGVzIDE4MyBvbiAzNS00NC4KQUdFX09W"
        "RVJSSURFID0gewogICAgIlJvY2tzdGFyIjogIjM1LTQ0IiwKICAgICJOT1MiOiAiMjUtNDQiLAog"
        "ICAgIkJhbmciOiAiMTgtMzQiLAp9CgojIEJyYW5kcyB3aG9zZSB6ZXJvLXN1Z2FyIGxpbmVzIHNl"
        "bGwgdG8gYSBkaWZmZXJlbnQgcGVyc29uIHRoYW4gdGhlIHN1Z2FyZWQKIyBwYXJlbnQuIE9ubHkg"
        "YXBwbGllcyB0byBtYWluc3RyZWFtIHN1Z2FyZWQgYnJhbmRzIOKAlCBhIHN1Z2FyLWZyZWUgR2hv"
        "c3QgaXMKIyBzdGlsbCBib3VnaHQgYnkgdGhlIHNhbWUgZ3ltLWdvZXIuClNQTElUX09OX1NVR0FS"
        "X0ZSRUUgPSB7CiAgICAiUmVkIEJ1bGwiLCAiTW9uc3RlciIsICJSb2Nrc3RhciIsICJOT1MiLCAi"
        "QU1QIiwgIk10biBEZXcgQU1QIiwKICAgICJGdWxsIFRocm90dGxlIiwgIlZlbm9tIiwgIlJpcCBJ"
        "dCIsICJNdG4gRGV3IChlbmVyZ3kpIiwgIkFyaXpvbmEgRW5lcmd5IiwKICAgICJSYXB0b3IiLCAi"
        "TGlxdWlkIEljZSIsICJBZHJlbmFsaW5lIFJ1c2giLCAiT2wnIEdsb3J5IiwgIkJ1bSBFbmVyZ3ki"
        "LAp9CgpTVUdBUl9GUkVFID0gcmUuY29tcGlsZSgKICAgIHIic3VnYXJbXHMtXT9mcmVlfHplcm98"
        "ZGlldHxsb3cgY2Fsb3JpZXxubyBzdWdhcnx1bHRyYSIsIHJlLkkpCk5BVFVSQUwgPSByZS5jb21w"
        "aWxlKHIib3JnYW5pY3x5ZXJiYXxtYXRlfGtvbWJ1Y2hhfGJvdGFuaWN8cGxhbnQiLCByZS5JKQpD"
        "T0ZGRUUgPSByZS5jb21waWxlKHIiY29mZmVlfGVzcHJlc3NvfGxhdHRlfGNvbGQgYnJld3xtb2No"
        "YXxjYXBwdWNjaW5vIiwgcmUuSSkKIyBcYiBtYXR0ZXJzIG9uIHRoZSBzaXplczogd2l0aG91dCBp"
        "dCAiMiBPWiIgbWF0Y2hlcyBpbnNpZGUgIjEyIE9aIi4KU0hPVCA9IHJlLmNvbXBpbGUociJcYnNo"
        "b3RcYnxcYjIgP296XGJ8XGIxXC45XGQ/ID9velxifFxiMlwuNSA/b3pcYiIsIHJlLkkpClBFUkZP"
        "Uk1BTkNFID0gcmUuY29tcGlsZSgKICAgIHIicHJlW1xzLV0/d29ya291dHxiY2FhfGFtaW5vfGNy"
        "ZWF0aW5lfHBlcmZvcm1hbmNlfFxicHVtcFxifFxiZml0XGJ8cHJvdGVpbiIsIHJlLkkpCgoKIyAt"
        "LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tIGZsYXZvciBmYW1pbGllcwojIDg2MCBkaXN0aW5jdCByYXcgZmxhdm9yIHN0cmluZ3MgY29s"
        "bGFwc2UgdG8gMTQgZmFtaWxpZXMuIE9yZGVyIG1hdHRlcnM6IHRoZQojIGZpcnN0IHBhdHRlcm4g"
        "dG8gbWF0Y2ggd2lucywgc28gdGhlIHNwZWNpZmljIG9uZXMgKFNvdXIvY2FuZHksIENvbGEpIHNp"
        "dCBhYm92ZQojIHRoZSBicm9hZCBmcnVpdCBidWNrZXRzIHRoYXQgd291bGQgb3RoZXJ3aXNlIHN3"
        "YWxsb3cgdGhlbS4KRkxBVk9SX0ZBTUlMSUVTID0gWwogICAgKCJPcmlnaW5hbCIsIHIiXGJvcmln"
        "fGNsYXNzaWN8XGJ0aGUgb3JpZ2luYWxcYnxyZWd1bGFyIiksCiAgICAoIkNvZmZlZSAmIGNyZWFt"
        "IiwgciJjb2ZmZWV8ZXNwcmVzc298bGF0dGV8bW9jaGF8Y2FwcHVjY2lub3x2YW5pbGxhfGNyZWFt"
        "KD8hc2ljbGUpfGNhcmFtZWx8aG9yY2hhdGEiKSwKICAgICgiU291ciAmIGNhbmR5IiwgciJzb3Vy"
        "fGNhbmR5fGd1bW15fGJ1YmJsZSA/Z3VtfGNvdHRvbnxyYXp6fHNsdXNofGZyZWV6ZXxyYWluYm93"
        "fCIKICAgICAgICAgICAgICAgICAgICAgIHIic3dlZGlzaCBmaXNofGJpcnRoZGF5IGNha2V8c2hl"
        "cmJldHxzb3JiZXR8bWFyc2htYWxsb3d8cyc/bW9yZSIpLAogICAgKCJDb2xhICYgc29kYSIsIHIi"
        "Y29sYXxyb290ID9iZWVyfGRyXC4/ID9wZXBwZXJ8Y3JlYW0gP3NvZGF8Z2luZ2VyIiksCiAgICAo"
        "IldhdGVybWVsb24iLCByIndhdGVybWVsb24iKSwKICAgICgiQmVycnkiLCByImJlcnJ5fGJlcnJp"
        "ZXN8cmFzcGJlcnJ5fGJsdWViZXJyeXxzdHJhd2JlcnJ8YmxhY2tiZXJyeXxhY2FpfGNyYW5iZXJy"
        "fGp1bmViZXJyeXxjaGVycnkiKSwKICAgICgiVHJvcGljYWwiLCByInRyb3BpY2FsfG1hbmdvfHBp"
        "bmVhcHBsZXxwYXNzaW9ufGd1YXZhfGNvY29udXR8cGFwYXlhfGRyYWdvbiA/ZnJ1aXR8a2l3aXxi"
        "YW5hbmF8aGF3YWlpIiksCiAgICAoIkNpdHJ1cyIsIHIiY2l0cnVzfG9yYW5nZXxsZW1vbnxsaW1l"
        "fGdyYXBlZnJ1aXR8dGFuZ2VyaW5lfGNsZW1lbnRpbmV8eXV6dSIpLAogICAgKCJHcmFwZSIsIHIi"
        "Z3JhcGUiKSwKICAgICgiQXBwbGUgJiBwZWFyIiwgciJhcHBsZXxwZWFyIiksCiAgICAoIlBlYWNo"
        "ICYgc3RvbmUgZnJ1aXQiLCByInBlYWNofGFwcmljb3R8bmVjdGFyaW5lfHBsdW18bWFuZ28gcGVh"
        "Y2giKSwKICAgICgiUHVuY2ggJiBtaXhlZCBmcnVpdCIsIHIicHVuY2h8ZnJ1aXR8bWVsb258bWl4"
        "ZWR8Ymxhc3R8YmxlbmR8bWVkbGV5IiksCiAgICAoIlRlYSAmIGJvdGFuaWNhbCIsIHIidGVhfG1h"
        "dGV8eWVyYmF8bWludHxtZW50aG9sfGxhdmVuZGVyfGhpYmlzY3VzfGdpbnNlbmd8bWF0Y2hhIiks"
        "CiAgICAoIk1lbG9uICYgb3RoZXIiLCByIm1lbG9ufGN1Y3VtYmVyfGhvbmV5ZGV3fGNhbnRhbG91"
        "cGUiKSwKXQpGTEFWT1JfUlggPSBbKG5hbWUsIHJlLmNvbXBpbGUocngsIHJlLkkpKSBmb3IgbmFt"
        "ZSwgcnggaW4gRkxBVk9SX0ZBTUlMSUVTXQoKCmRlZiBmbGF2b3JfZmFtaWx5KHJvdyk6CiAgICAi"
        "IiIKICAgIEdyb3VwIHRoZSByYXcgZmxhdm9yIGludG8gb25lIG9mIDE0IGZhbWlsaWVzLgoKICAg"
        "IEZMQVZPUiBpcyBibGFuayBvbiA0OTkgb2YgMiwzMDkgU0tVcywgc28gZmFsbCBiYWNrIHRvIHRo"
        "ZSBwcm9kdWN0CiAgICBkZXNjcmlwdGlvbiwgd2hpY2ggdXN1YWxseSBuYW1lcyB0aGUgZmxhdm9y"
        "IGlubGluZQogICAgKCJSRUQgQlVMTCBXQVRFUk1FTE9OIEVORVJHWSBEUklOSyAxMiBPWiBDQU4i"
        "KS4KICAgICIiIgogICAgcmF3ID0gKHJvdy5nZXQoIkZMQVZPUiIpIG9yICIiKS5zdHJpcCgpCiAg"
        "ICB0ZXh0ID0gcmF3IG9yIChyb3cuZ2V0KCJQUk9EVUNUX0RFU0NSSVBUSU9OIikgb3IgIiIpCiAg"
        "ICBpZiBub3QgdGV4dC5zdHJpcCgpOgogICAgICAgIHJldHVybiAiVW5zcGVjaWZpZWQiCiAgICBm"
        "b3IgbmFtZSwgcnggaW4gRkxBVk9SX1JYOgogICAgICAgIGlmIHJ4LnNlYXJjaCh0ZXh0KToKICAg"
        "ICAgICAgICAgcmV0dXJuIG5hbWUKICAgICMgQSBuYW1lZCBmbGF2b3IgdGhhdCBtYXRjaGVzIG5v"
        "dGhpbmcgaXMgbm90IGEgZ2FwIGluIHRoZSBydWxlcyDigJQgaXQgaXMgYW4KICAgICMgaW52ZW50"
        "ZWQgbmFtZSAoRnJvc2UgUm9zZSwgQ29zbWljIFN0YXJkdXN0LCBXaXRjaCdzIEJyZXcpLiBUaGF0"
        "IGlzIE1pbnRlbCdzCiAgICAjICJicmFuZGVkIGZsYXZvcnMiIHRyZW5kLCBzbyBpdCBnZXRzIGl0"
        "cyBvd24gZmFtaWx5IHJhdGhlciB0aGFuIGEganVuayBidWNrZXQuCiAgICByZXR1cm4gIk5vdmVs"
        "dHkgJiBicmFuZGVkIiBpZiByYXcgZWxzZSAiVW5zcGVjaWZpZWQiCgoKZGVmIGJsb2Iocm93KToK"
        "ICAgICIiIkV2ZXJ5dGhpbmcgdGV4dHVhbCBhYm91dCB0aGUgU0tVLCBmb3IgdGhlIGF0dHJpYnV0"
        "ZSBydWxlcyB0byByZWFkLiIiIgogICAgcmV0dXJuICIgIi5qb2luKAogICAgICAgIHJvdy5nZXQo"
        "YywgIiIpIG9yICIiIGZvciBjIGluCiAgICAgICAgKCJQUk9EVUNUX0RFU0NSSVBUSU9OIiwgIkZM"
        "QVZPUiIsICJQUk9EVUNUX1RZUEUiLCAiU1VCX1BST0RVQ1RfVFlQRSIsCiAgICAgICAgICJVTklU"
        "X1NJWkUiLCAiUEFDS0FHRSIsICJCUkFORCIpCiAgICApCgoKZGVmIGNsYXNzaWZ5KHJvdyk6CiAg"
        "ICAiIiItPiAoYXVkaWVuY2UsIGFnZSkuIEJyYW5kIGZpcnN0LCB0aGVuIHByb2R1Y3QgYXR0cmli"
        "dXRlcy4iIiIKICAgIGJyYW5kID0gKHJvdy5nZXQoImNhbm9uaWNhbF9icmFuZCIpIG9yICIiKS5z"
        "dHJpcCgpCiAgICB0ZXh0ID0gYmxvYihyb3cpCiAgICBwdHlwZSA9IHJvdy5nZXQoIlBST0RVQ1Rf"
        "VFlQRSIpIG9yICIiCiAgICBzdWIgPSByb3cuZ2V0KCJTVUJfUFJPRFVDVF9UWVBFIikgb3IgIiIK"
        "ICAgIHN1Z2FyX2ZyZWUgPSBib29sKFNVR0FSX0ZSRUUuc2VhcmNoKHN1Yikgb3IgU1VHQVJfRlJF"
        "RS5zZWFyY2godGV4dCkpCgogICAgYXVkID0gQlJBTkQuZ2V0KGJyYW5kKQogICAgaWYgYXVkOgog"
        "ICAgICAgIGlmIHN1Z2FyX2ZyZWUgYW5kIGJyYW5kIGluIFNQTElUX09OX1NVR0FSX0ZSRUU6CiAg"
        "ICAgICAgICAgIHJldHVybiAiQ2Fsb3JpZS1jdXR0ZXJzIiwgQVVESUVOQ0VbIkNhbG9yaWUtY3V0"
        "dGVycyJdWzBdCiAgICAgICAgcmV0dXJuIGF1ZCwgQUdFX09WRVJSSURFLmdldChicmFuZCwgQVVE"
        "SUVOQ0VbYXVkXVswXSkKCiAgICAjIC0tLS0gYXR0cmlidXRlIGZhbGxiYWNrIGZvciB0aGUgfjE5"
        "MCBicmFuZHMgd2l0aCBubyBwdWJsaXNoZWQgYXVkaWVuY2UgLS0tLQogICAgaWYgU0hPVC5zZWFy"
        "Y2godGV4dCkgb3IgIlNob3QiIGluIHB0eXBlOgogICAgICAgIGF1ZCA9ICJPbGRlciBmdW5jdGlv"
        "bmFsIHVzZXJzIgogICAgZWxpZiBDT0ZGRUUuc2VhcmNoKHRleHQpIG9yICJDb2ZmZWUiIGluIHB0"
        "eXBlOgogICAgICAgIGF1ZCA9ICJDb2ZmZWUgZHJpbmtlcnMiCiAgICBlbGlmIE5BVFVSQUwuc2Vh"
        "cmNoKHRleHQpIG9yICJPcmdhbmljIiBpbiBwdHlwZSBvciAiWWVyYmEiIGluIHB0eXBlOgogICAg"
        "ICAgIGF1ZCA9ICJIZWFsdGgtY29uc2Npb3VzIGFkdWx0cyIKICAgIGVsaWYgUEVSRk9STUFOQ0Uu"
        "c2VhcmNoKHRleHQpOgogICAgICAgIGF1ZCA9ICJHeW0gJiBmaXRuZXNzIgogICAgZWxpZiBzdWdh"
        "cl9mcmVlOgogICAgICAgIGF1ZCA9ICJDYWxvcmllLWN1dHRlcnMiCiAgICBlbHNlOgogICAgICAg"
        "IGF1ZCA9ICJZb3VuZyBhZHVsdHMiCiAgICByZXR1cm4gYXVkLCBBVURJRU5DRVthdWRdWzBdCgoK"
        "ZGVmIG1haW4oKToKICAgIHBhdGggPSBvcy5wYXRoLm5vcm1wYXRoKFNSQykKICAgIHdpdGggb3Bl"
        "bihwYXRoLCBuZXdsaW5lPSIiKSBhcyBmaDoKICAgICAgICByb3dzID0gbGlzdChjc3YuRGljdFJl"
        "YWRlcihmaCkpCiAgICBpZiBub3Qgcm93czoKICAgICAgICBzeXMuZXhpdCgibm8gcm93cyBpbiAi"
        "ICsgcGF0aCkKCiAgICAjIGRyb3AgYW55IGNvbHVtbnMgZnJvbSBhIHByZXZpb3VzIHJ1biwgaW5j"
        "bHVkaW5nIHRoZSBvbGRlciBzY2hlbWEKICAgIHN0YWxlID0gc2V0KEFEREVEKSB8IHsidGFyZ2V0"
        "X2NvbnN1bWVyX2RldGFpbCIsICJ0YXJnZXRfZXZpZGVuY2UifQogICAgYmFzZSA9IFtjIGZvciBj"
        "IGluIHJvd3NbMF0ua2V5cygpIGlmIGMgbm90IGluIHN0YWxlXQoKICAgIGZvciByIGluIHJvd3M6"
        "CiAgICAgICAgYXVkLCBhZ2UgPSBjbGFzc2lmeShyKQogICAgICAgIF8sIGdlbmRlciwgbm90ZSA9"
        "IEFVRElFTkNFW2F1ZF0KICAgICAgICBicmFuZCA9IChyLmdldCgiY2Fub25pY2FsX2JyYW5kIikg"
        "b3IgIiIpLnN0cmlwKCkKICAgICAgICAjIGEgYnJhbmQtc3BlY2lmaWMgbm90ZSBvbmx5IGFwcGxp"
        "ZXMgd2hpbGUgdGhlIFNLVSBzdGlsbCBzaXRzIGluIHRoYXQKICAgICAgICAjIGJyYW5kJ3Mgb3du"
        "IGF1ZGllbmNlIC0gYSBzdWdhci1mcmVlIE1vbnN0ZXIgaXMgYSBjYWxvcmllLWN1dHRlciBub3cK"
        "ICAgICAgICBpZiBicmFuZCBpbiBCUkFORF9OT1RFIGFuZCBhdWQgPT0gQlJBTkQuZ2V0KGJyYW5k"
        "KToKICAgICAgICAgICAgbm90ZSA9IEJSQU5EX05PVEVbYnJhbmRdCiAgICAgICAgclsidGFyZ2V0"
        "X2NvbnN1bWVyIl0gPSBhdWQKICAgICAgICByWyJ0YXJnZXRfYWdlIl0gPSBhZ2UKICAgICAgICBy"
        "WyJ0YXJnZXRfZ2VuZGVyIl0gPSBnZW5kZXIKICAgICAgICByWyJ0YXJnZXRfbm90ZXMiXSA9IG5v"
        "dGUKICAgICAgICByWyJmbGF2b3JfZmFtaWx5Il0gPSBmbGF2b3JfZmFtaWx5KHIpCgogICAgd2l0"
        "aCBvcGVuKHBhdGgsICJ3IiwgbmV3bGluZT0iIikgYXMgZmg6CiAgICAgICAgdyA9IGNzdi5EaWN0"
        "V3JpdGVyKGZoLCBmaWVsZG5hbWVzPWJhc2UgKyBBRERFRCwgZXh0cmFzYWN0aW9uPSJpZ25vcmUi"
        "KQogICAgICAgIHcud3JpdGVoZWFkZXIoKQogICAgICAgIHcud3JpdGVyb3dzKHJvd3MpCiAgICBw"
        "cmludChmImxhYmVsbGVkIHtsZW4ocm93cyl9IFNLVXMgLT4ge3BhdGh9IikKCgppZiBfX25hbWVf"
        "XyA9PSAiX19tYWluX18iOgogICAgbWFpbigpCg=="
    ),
    "flavor_mentions": (
        "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiJGbGF2b3IgKyBicmFuZCBtZW50aW9uIGV4dHJhY3Rp"
        "b24gZnJvbSBmcmVlIHRleHQuIFdvcmtzdHJlYW0gMywgaXRlbSAzLgoKU2hhcmVkIGJ5IGV2ZXJ5"
        "IHRleHQgc291cmNlLCBzbyBSZWRkaXQgYW5kIFlvdVR1YmUgYXJlIHNjb3JlZCBieSBpZGVudGlj"
        "YWwKcnVsZXMgYW5kIHRoZWlyIG51bWJlcnMgY2FuIHNpdCBpbiB0aGUgc2FtZSB0YWJsZS4gSW1w"
        "b3J0YWJsZSBhcyBhIG1vZHVsZTsKcnVubmFibGUgZGlyZWN0bHkgdG8gc2VlIHdoYXQgaXQgZG9l"
        "cyB0byByZWFsIHRleHQ6CgogICAgcHl0aG9uIGNhcHN0b25lL2NvbGxlY3RvcnMvZmxhdm9yX21l"
        "bnRpb25zLnB5IC0tZGVtbyBkYXRhL3lvdXR1YmUvY29tbWVudHMuY3N2IC0tbGltaXQgNDAwMDAK"
        "ClRIRSBBTElBUyBQUk9CTEVNLCBXSElDSCBJUyBNT1NUIE9GIFRIRSBXT1JLCi0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tClBlb3BsZSBkbyBub3Qgd3JpdGUgIkJs"
        "dWUgUmFzcGJlcnJ5Ii4gVGhleSB3cml0ZSBibHVlIHJhenosIGJsdSByYXp6LCBibHVlcmF6eiwK"
        "InRoZSBibHVlIG9uZSIuIEEgbWF0Y2hlciBidWlsdCBvbiB0aGUgY2Fub25pY2FsIEZMQVZPUiBz"
        "dHJpbmdzIGFsb25lIGZpbmRzIGEKZnJhY3Rpb24gb2YgcmVhbCBtZW50aW9ucyBhbmQgZmluZHMg"
        "aXQgdW5ldmVubHkgLSBmbGF2b3JzIHdpdGggc2hvcnQgaW5mb3JtYWwKbmFtZXMgbG9zZSBoYXJk"
        "ZXN0LCB3aGljaCBiaWFzZXMgdGhlIHZlcnkgcmFua2luZyB0aGlzIGZlZWRzLiBTbyB0aGUgYWxp"
        "YXMgdGFibGUKYmVsb3cgaXMgdGhlIGRlbGl2ZXJhYmxlLCBhbmQgaXQgaXMgZGVsaWJlcmF0ZWx5"
        "IGV4cGxpY2l0IHJhdGhlciB0aGFuIGZ1enp5OgpldmVyeSBhbGlhcyBpcyB3cml0dGVuIGRvd24g"
        "YW5kIGF1ZGl0YWJsZSwgYmVjYXVzZSBhIGNvbW1pdHRlZSBjYW4gYXNrIHdoeSBhCmNvbW1lbnQg"
        "Y291bnRlZCBhbmQgdGhlIGFuc3dlciBoYXMgdG8gYmUgYSBydWxlLCBub3QgYW4gZWRpdCBkaXN0"
        "YW5jZS4KCldIQVQgSVMgREVMSUJFUkFURUxZIE5PVCBET05FCi0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tCk5vIHN0ZW1taW5nLCBubyBmdXp6eS9MZXZlbnNodGVpbiBtYXRjaGluZywgbm8g"
        "ZW1iZWRkaW5nIHNpbWlsYXJpdHkuIEVhY2ggd291bGQKcmFpc2UgcmVjYWxsIGFuZCBkZXN0cm95"
        "IHRoZSBhdWRpdCB0cmFpbCAtICJ3aHkgZGlkIHRoaXMgY291bnQiIHN0b3BzIGhhdmluZyBhbgph"
        "bnN3ZXIgYSBodW1hbiBjYW4gY2hlY2suIFByZWNpc2lvbiBpcyB2YWxpZGF0ZWQgYnkgaGFuZC1s"
        "YWJlbGxpbmcgaW5zdGVhZAooV29ya3N0cmVhbSAzIGl0ZW0gNCkuCgpORUdBVElPTiBBTkQgQ09O"
        "VEVYVCBBUkUgTk9UIEhBTkRMRUQgSEVSRS4gIm5vdCBhIGZhbiBvZiBtYW5nbyIgY291bnRzIGFz"
        "IGEKbWFuZ28gbWVudGlvbi4gTWVudGlvbiBzaGFyZSBtZWFzdXJlcyBBVFRFTlRJT04sIG5vdCBh"
        "cHByb3ZhbDsgc2VudGltZW50IGlzCnNjb3JlZCBzZXBhcmF0ZWx5IGFuZCB0aGUgdHdvIGFyZSBy"
        "ZXBvcnRlZCBzZXBhcmF0ZWx5LiBDb25mbGF0aW5nIHRoZW0gaXMgaG93IGEKaGF0ZWQgZmxhdm9y"
        "IGJlY29tZXMgYSByZWNvbW1lbmRhdGlvbi4KClBSSVZBQ1kKLS0tLS0tLQpVc2VybmFtZXMgbmV2"
        "ZXIgZW50ZXIgdGhlIG91dHB1dCBhbmQgcmF3IGNvbW1lbnQgdGV4dCBpcyBuZXZlciB3cml0dGVu"
        "IHRvIGRpc2sKYnkgdGhpcyBtb2R1bGUuIENhbGxlcnMgZ2V0IGNvdW50cyBhbmQgcGVyLW1lbnRp"
        "b24gc2VudGltZW50LCBrZXllZCBieSBmbGF2b3IuCiIiIgppbXBvcnQgYXJncGFyc2UKaW1wb3J0"
        "IGNvbGxlY3Rpb25zCmltcG9ydCBjc3YKaW1wb3J0IG9zCmltcG9ydCByZQppbXBvcnQgc3lzCgpS"
        "T09UID0gb3MucGF0aC5kaXJuYW1lKG9zLnBhdGguZGlybmFtZShvcy5wYXRoLmRpcm5hbWUob3Mu"
        "cGF0aC5hYnNwYXRoKF9fZmlsZV9fKSkpKQpzeXMucGF0aC5pbnNlcnQoMCwgb3MucGF0aC5qb2lu"
        "KFJPT1QsICJkYXRhL3NjcmlwdHMiKSkKZnJvbSBjbGFzc2lmeV90YXJnZXRfY29uc3VtZXJzIGlt"
        "cG9ydCBmbGF2b3JfZmFtaWx5ICAjIG5vcWE6IEU0MDIKCiMgLS0tIGZsYXZvciBhbGlhc2VzIC0t"
        "LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLQoj"
        "IGNhbm9uaWNhbCBmbGF2b3IgLT4gc3BlbGxpbmdzIHNlZW4gaW4gdGhlIHdpbGQuIExvd2VyY2Fz"
        "ZTsgbWF0Y2hlZCBhcyB3aG9sZQojIHdvcmRzIChzZWUgV09SRCBiZWxvdyksIHNvICJncmFwZSIg"
        "ZG9lcyBub3QgZmlyZSBpbnNpZGUgImdyYXBlZnJ1aXQiLgojCiMgU291cmNlcyBmb3IgdGhlc2U6"
        "IHRoZSBGTEFWT1Igc3RyaW5ncyBpbiB0aGUgUERJIFNLVSBsaXN0LCBwbHVzIHRoZSBpbmZvcm1h"
        "bAojIGZvcm1zIHRoYXQgYWN0dWFsbHkgYXBwZWFyIGluIHRoZSBZb3VUdWJlIGNvcnB1cy4gQWRk"
        "IHRvIHRoaXMgdGFibGUgcmF0aGVyCiMgdGhhbiBsb29zZW5pbmcgdGhlIG1hdGNoZXIuCkZMQVZP"
        "Ul9BTElBU0VTID0gewogICAgIkJsdWUgUmFzcGJlcnJ5IjogWyJibHVlIHJhc3BiZXJyeSIsICJi"
        "bHVlIHJhenoiLCAiYmx1IHJhenoiLCAiYmx1ZXJhenoiLAogICAgICAgICAgICAgICAgICAgICAg"
        "ICJibHVlIHJhc3AiLCAiYmx1ZXJhc3BiZXJyeSJdLAogICAgIldhdGVybWVsb24iOiAgICAgWyJ3"
        "YXRlcm1lbG9uIiwgIndhdGVyIG1lbG9uIiwgInd0cm1sbiJdLAogICAgIk1hbmdvIjogICAgICAg"
        "ICAgWyJtYW5nbyIsICJtYW5nb3MiLCAibWFuZ29lcyJdLAogICAgIlN0cmF3YmVycnkiOiAgICAg"
        "WyJzdHJhd2JlcnJ5IiwgInN0cmF3YmVycmllcyIsICJzdHJhd2IiXSwKICAgICJDaGVycnkiOiAg"
        "ICAgICAgIFsiY2hlcnJ5IiwgImNoZXJyaWVzIiwgImJsYWNrIGNoZXJyeSJdLAogICAgIlBlYWNo"
        "IjogICAgICAgICAgWyJwZWFjaCIsICJwZWFjaGVzIl0sCiAgICAiR3JhcGUiOiAgICAgICAgICBb"
        "ImdyYXBlIiwgImdyYXBlcyJdLAogICAgIk9yYW5nZSI6ICAgICAgICAgWyJvcmFuZ2UiLCAib3Jh"
        "bmdlcyJdLAogICAgIkxlbW9uIExpbWUiOiAgICAgWyJsZW1vbiBsaW1lIiwgImxlbW9uLWxpbWUi"
        "LCAibGVtb25saW1lIiwgImxpbWUiXSwKICAgICJQaW5lYXBwbGUiOiAgICAgIFsicGluZWFwcGxl"
        "IiwgInBpbmVhcHBsZXMiXSwKICAgICJUcm9waWNhbCI6ICAgICAgIFsidHJvcGljYWwiLCAidHJv"
        "cGljIl0sCiAgICAiRnJ1aXQgUHVuY2giOiAgICBbImZydWl0IHB1bmNoIiwgImZydWl0cHVuY2gi"
        "LCAicHVuY2giXSwKICAgICJDb3R0b24gQ2FuZHkiOiAgIFsiY290dG9uIGNhbmR5IiwgImNvdHRv"
        "bmNhbmR5Il0sCiAgICAiU291ciI6ICAgICAgICAgICBbInNvdXIiLCAic291ciBjYW5keSIsICJz"
        "b3VyIGd1bW15Il0sCiAgICAiVmFuaWxsYSI6ICAgICAgICBbInZhbmlsbGEiLCAidmFuaWxhIl0s"
        "CiAgICAiQ29mZmVlIjogICAgICAgICBbImNvZmZlZSIsICJsYXR0ZSIsICJtb2NoYSIsICJlc3By"
        "ZXNzbyJdLAogICAgIkNvbGEiOiAgICAgICAgICAgWyJjb2xhIiwgImNva2UgZmxhdm9yIiwgInJv"
        "b3QgYmVlciJdLAogICAgIkdyZWVuIEFwcGxlIjogICAgWyJncmVlbiBhcHBsZSIsICJncmVlbmFw"
        "cGxlIiwgInNvdXIgYXBwbGUiXSwKICAgICJQaW5hIENvbGFkYSI6ICAgIFsicGluYSBjb2xhZGEi"
        "LCAicGnDsWEgY29sYWRhIiwgInBpbmFjb2xhZGEiXSwKICAgICJEcmFnb24gRnJ1aXQiOiAgIFsi"
        "ZHJhZ29uIGZydWl0IiwgImRyYWdvbmZydWl0IiwgInBpdGF5YSJdLAogICAgIktpd2kiOiAgICAg"
        "ICAgICAgWyJraXdpIiwgImtpd2lzIl0sCiAgICAiR3VhdmEiOiAgICAgICAgICBbImd1YXZhIl0s"
        "CiAgICAiUGFzc2lvbmZydWl0IjogICBbInBhc3Npb25mcnVpdCIsICJwYXNzaW9uIGZydWl0Il0s"
        "CiAgICAiQ29jb251dCI6ICAgICAgICBbImNvY29udXQiXSwKICAgICJNaW50IjogICAgICAgICAg"
        "IFsibWludCIsICJtZW50aG9sIiwgInNwZWFybWludCJdLAogICAgIk9yaWdpbmFsIjogICAgICAg"
        "WyJvcmlnaW5hbCIsICJvZyBmbGF2b3IiLCAiY2xhc3NpYyBmbGF2b3IiLCAidGhlIG9yaWdpbmFs"
        "Il0sCiAgICAiWmVybyBTdWdhciI6ICAgICBbInplcm8gc3VnYXIiLCAic3VnYXIgZnJlZSIsICJz"
        "dWdhcmZyZWUiLCAiemVybyB1bHRyYSJdLAp9CgojIC0tLSBicmFuZCBhbGlhc2VzIC0tLS0tLS0t"
        "LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0KIyBNaXJy"
        "b3JzIHRoZSBjYW5vbmljYWwgc2V0IGluIGRhdGEvc2NyYXBlcnMvY29tbW9uLnB5LiBLZXB0IGhl"
        "cmUgc28gdGhlIHRleHQKIyBwaXBlbGluZSBoYXMgb25lIHRhYmxlIHJhdGhlciB0aGFuIGltcG9y"
        "dGluZyBhIHNjcmFwZXIuCkJSQU5EX0FMSUFTRVMgPSB7CiAgICAiUmVkIEJ1bGwiOiAgWyJyZWQg"
        "YnVsbCIsICJyZWRidWxsIiwgInJiIl0sCiAgICAiTW9uc3RlciI6ICAgWyJtb25zdGVyIiwgIm1v"
        "bnN0ZXIgZW5lcmd5Il0sCiAgICAiQ2Vsc2l1cyI6ICAgWyJjZWxzaXVzIl0sCiAgICAiQWxhbmkg"
        "TnUiOiAgWyJhbGFuaSBudSIsICJhbGFuaSIsICJhbGFuaW51Il0sCiAgICAiQzQiOiAgICAgICAg"
        "WyJjNCIsICJjNCBlbmVyZ3kiXSwKICAgICJHaG9zdCI6ICAgICBbImdob3N0IiwgImdob3N0IGVu"
        "ZXJneSJdLAogICAgIlJvY2tzdGFyIjogIFsicm9ja3N0YXIiLCAicm9jayBzdGFyIl0sCiAgICAi"
        "Tk9TIjogICAgICAgWyJub3MiXSwKICAgICJSZWlnbiI6ICAgICBbInJlaWduIl0sCiAgICAiQmFu"
        "ZyI6ICAgICAgWyJiYW5nIiwgImJhbmcgZW5lcmd5Il0sCiAgICAiUHJpbWUiOiAgICAgWyJwcmlt"
        "ZSIsICJwcmltZSBlbmVyZ3kiXSwKICAgICJHZnVlbCI6ICAgICBbImdmdWVsIiwgImcgZnVlbCIs"
        "ICJnLWZ1ZWwiXSwKICAgICJCdWNrZWQgVXAiOiBbImJ1Y2tlZCB1cCIsICJidWNrZWR1cCJdLAp9"
        "CgojIFRFUk1TIFRIQVQgTE9PSyBMSUtFIEEgSElUIEFORCBBUkUgTk9ULiBFYWNoIG9mIHRoZXNl"
        "IHdhcyBmb3VuZCBmaXJpbmcgaW4gdGhlCiMgWW91VHViZSBjb3JwdXMuIFdpdGhvdXQgdGhlbSB0"
        "aGUgY291bnRzIGFyZSB3cm9uZyBpbiBhIGRpcmVjdGlvbiB0aGF0IGlzIGVhc3kKIyB0byBtaXNz"
        "LCBiZWNhdXNlIHRoZSBmYWxzZSBoaXRzIGNvbmNlbnRyYXRlIG9uIGEgaGFuZGZ1bCBvZiBmbGF2"
        "b3JzLgojCiMgICAibW9uc3RlciIgLT4gdGhlIGZpbG0vY3JlYXR1cmUgc2Vuc2UsIGFuZCBFbWlu"
        "ZW0ncyAiVGhlIE1vbnN0ZXIiCiMgICAiYmFuZyIgICAgLT4gdGhlIG5vaXNlLCAiYmFuZyBmb3Ig"
        "eW91ciBidWNrIiwgImJhbmcgb24iLCAiYmlnIGJhbmciLCBhbmQKIyAgICAgICAgICAgICAgICBw"
        "bHVyYWwgImJhbmdzIiAoaGFpcikgLSB0aGUgYnJhbmQgaXMgYWx3YXlzIHNpbmd1bGFyLgojICAg"
        "ICAgICAgICAgICAgIEFuIGVhcmxpZXIgdmVyc2lvbiB1c2VkIGBiYW5ncz9cYig/ISBlbmVyZ3kp"
        "YCwgd2hpY2ggc3RyaXBwZWQKIyAgICAgICAgICAgICAgICBFVkVSWSAiYmFuZyIgbm90IGZvbGxv"
        "d2VkIGJ5ICJlbmVyZ3kiIGFuZCBzaWxlbnRseSBkZWxldGVkCiMgICAgICAgICAgICAgICAgcmVh"
        "bCBicmFuZCBtZW50aW9ucyBsaWtlICJ0aGUgYmFuZyBtb2NoYSB3YXMgdGhlIGdyZWF0ZXN0CiMg"
        "ICAgICAgICAgICAgICAgZmxhdm9yIG91dCIuIFRoZSBzZWxmLXRlc3QgaW4gcnVuX3JlZGRpdF9k"
        "ZWVwLnB5IGNhdWdodCBpdC4KIyAgICAgICAgICAgICAgICBTcGVjaWZpYyBwaHJhc2VzIG9ubHk7"
        "IG5ldmVyIGEgY2F0Y2gtYWxsIG9uIGEgYnJhbmQgbmFtZS4KIyAgICJwcmltZSIgICAtPiBBbWF6"
        "b24gUHJpbWUsICJwcmltZSB0aW1lIiwgImluIGhpcyBwcmltZSIKIyAgICJub3MiICAgICAtPiBu"
        "aXRyb3VzIG94aWRlLCAibm9zIiBpbiByYWNpbmcgdGFsawojICAgInJiIiAgICAgIC0+IFJCIExl"
        "aXB6aWcsIHJ1bm5pbmcgYmFjawpOT0lTRSA9IHJlLmNvbXBpbGUoCiAgICByIlxiKHRoZSBtb25z"
        "dGVyfG1vbnN0ZXIgbW92aWV8bW9uc3RlcnM/IGluY3xsb2NoIG5lc3N8IgogICAgciJiYW5nIGZv"
        "ciB5b3VyIGJ1Y2t8YmFuZyBvbnxiaWcgYmFuZ3xcYmJhbmdzXGJ8IgogICAgciJhbWF6b24gcHJp"
        "bWV8cHJpbWUgdGltZXxwcmltZSB2aWRlb3xpbiBoaXMgcHJpbWV8aW4gaGVyIHByaW1lfHByaW1l"
        "IHJpYnwiCiAgICByIm5pdHJvdXN8bm9zIGJvdHRsZXwiCiAgICByInJiIGxlaXB6aWd8cnVubmlu"
        "ZyBiYWNrKVxiIiwgcmUuSSkKCgojIFRFUk1TIFRIQVQgQVJFIEFMU08gU1RBTkRBTE9ORSBCRVZF"
        "UkFHRVMgT1IgRk9PRFMuCiMKIyBGb3VuZCBieSBzcG90LWNoZWNraW5nIHRoZSBtYXRjaGVyIGFn"
        "YWluc3QgdGhlIFlvdVR1YmUgY29ycHVzOiAiQ29mZmVlIiBjYW1lCiMgYmFjayBhcyB0aGUgIzEg"
        "Zmxhdm9yIGF0IDIzJSBtZW50aW9uIHNoYXJlLCBhbmQgaGFuZC1yZWFkaW5nIHRoZSBmaXJzdCB0"
        "d2VsdmUKIyBoaXRzIHNob3dlZCBBTEwgdHdlbHZlIHdlcmUgcGVvcGxlIGRpc2N1c3NpbmcgY29m"
        "ZmVlIGFzIGEgY29tcGV0aW5nIGRyaW5rCiMgKCJJIG9ubHkgaGF2ZSAxIGN1cCBvZiBjb2ZmZWUg"
        "aW4gdGhlIG1vcm5pbmciLCAiSSBkb24ndCBkcmluayBjb2ZmZWUgb3IKIyBzb2RhIikuIE5vdCBv"
        "bmUgd2FzIGEgY29mZmVlLUZMQVZPUkVEIGVuZXJneSBkcmluay4KIwojIFRoZXNlIHRlcm1zIG9u"
        "bHkgY291bnQgd2hlbiB0aGUgY29tbWVudCBhbHNvIHN1cHBsaWVzIHByb2R1Y3QgY29udGV4dDog"
        "YQojIGJyYW5kIG5hbWUsIG9yIGEgd29yZCB0aGF0IG1hcmtzIHRoZSB0ZXJtIGFzIGRlc2NyaWJp"
        "bmcgYSBmbGF2b3IuIFRoZSBnYXRlIGlzCiMgYSB3cml0dGVuIHJ1bGUgcmF0aGVyIHRoYW4gYSB0"
        "aHJlc2hvbGQsIHNvIGFueSBzaW5nbGUgbWF0Y2ggY2FuIGJlIGV4cGxhaW5lZC4KIwojIFRlcm1z"
        "IGxpa2UgIndhdGVybWVsb24iIG9yICJibHVlIHJhenoiIGRvIG5vdCBuZWVkIHRoZSBnYXRlIC0g"
        "bm9ib2R5IGRpc2N1c3NlcwojIGRyaW5raW5nIGEgd2F0ZXJtZWxvbiBhcyBhbiBhbHRlcm5hdGl2"
        "ZSB0byBhbiBlbmVyZ3kgZHJpbmsuCkFNQklHVU9VUyA9IHsiQ29mZmVlIiwgIkNvbGEiLCAiT3Jp"
        "Z2luYWwiLCAiTWludCIsICJaZXJvIFN1Z2FyIiwgIlNvdXIiLAogICAgICAgICAgICAgIk9yYW5n"
        "ZSIsICJHcmFwZSIsICJDaGVycnkiLCAiTGVtb24gTGltZSJ9CgojIFRoZSBtYXJrZXIgbXVzdCBz"
        "aXQgTkVBUiB0aGUgdGVybSwgbm90IG1lcmVseSBzb21ld2hlcmUgaW4gdGhlIHNhbWUgY29tbWVu"
        "dC4KIwojIENvLXByZXNlbmNlIHdhcyB0cmllZCBmaXJzdCBhbmQgd2FzIG5vdCBlbm91Z2g6IGl0"
        "IGxlZnQgIkkgY2FuIG9ubHkgZHJpbmsKIyBkZWNhZiBjb2ZmZWUiIGNvdW50aW5nIGFzIGEgY29m"
        "ZmVlIGZsYXZvciwgYmVjYXVzZSBhIGJhcmUgYGNhbnM/YCBwYXR0ZXJuCiMgbWF0Y2hlcyB0aGUg"
        "bW9kYWwgdmVyYiAiY2FuIiwgYW5kICJkcmluayBhIiBtYXRjaGVkIGFueSBtZW50aW9uIG9mIGRy"
        "aW5raW5nLgojIEJvdGggYXJlIG5vdyBnb25lLiBXaGF0IHJlbWFpbnMgb25seSBkZXNjcmliZXMg"
        "YSBwcm9kdWN0J3MgdGFzdGUuCkZMQVZPUl9NQVJLRVIgPSByZS5jb21waWxlKAogICAgciJcYihm"
        "bGF2b3U/cnM/fGZsYXZvdT9yZWR8dGFzdGVzP3x0YXN0ZWR8dGFzdGluZ3wiCiAgICByIig/OmF8"
        "dGhlfFxkK1xzKm96KVxzK2NhbnM/XGJ8Y2Fucz8gb2Z8IgogICAgciJ2ZXJzaW9ufGVkaXRpb258"
        "dmFyaWFudClcYiIsIHJlLkkpCgojIEhvdyBmYXIgYSBtYXJrZXIgb3IgYnJhbmQgbWF5IHNpdCBm"
        "cm9tIGFuIGFtYmlndW91cyB0ZXJtIGFuZCBzdGlsbCBsaWNlbnNlIGl0LgojIDYwIGNoYXJhY3Rl"
        "cnMgaXMgYWJvdXQgb25lIGNsYXVzZSBlaXRoZXIgc2lkZSAtICJ0aGUgY29mZmVlIGZsYXZvciBv"
        "bmUiIGFuZAojICJNb25zdGVyJ3MgY29mZmVlIGxpbmUiIHBhc3M7IGEgY29tbWVudCB0aGF0IG1l"
        "bnRpb25zIFJlZCBCdWxsIGluIHNlbnRlbmNlIG9uZQojIGFuZCBkcmlua2luZyBjb2ZmZWUgaW4g"
        "c2VudGVuY2UgZm91ciBkb2VzIG5vdC4KQ09OVEVYVF9XSU5ET1cgPSA2MAoKCmRlZiBfbGljZW5z"
        "ZWQoY2xlYW4sIG1hdGNoLCBicmFuZHNfc3BhbnMpOgogICAgIiIiSXMgdGhpcyBhbWJpZ3VvdXMg"
        "bWF0Y2ggY2xvc2UgZW5vdWdoIHRvIGEgbWFya2VyIG9yIGEgYnJhbmQ/IiIiCiAgICBsbyA9IG1h"
        "eCgwLCBtYXRjaC5zdGFydCgpIC0gQ09OVEVYVF9XSU5ET1cpCiAgICBoaSA9IG1pbihsZW4oY2xl"
        "YW4pLCBtYXRjaC5lbmQoKSArIENPTlRFWFRfV0lORE9XKQogICAgaWYgRkxBVk9SX01BUktFUi5z"
        "ZWFyY2goY2xlYW4sIGxvLCBoaSk6CiAgICAgICAgcmV0dXJuIFRydWUKICAgIHJldHVybiBhbnko"
        "YnMgPCBoaSBhbmQgYmUgPiBsbyBmb3IgYnMsIGJlIGluIGJyYW5kc19zcGFucykKCgpkZWYgX3Bh"
        "dHRlcm4oYWxpYXNlcyk6CiAgICAiIiJXaG9sZS13b3JkIGFsdGVybmF0aW9uLCBsb25nZXN0LWZp"
        "cnN0IHNvICdibHVlIHJhenonIHdpbnMgb3ZlciAncmF6eicuIiIiCiAgICBwYXJ0cyA9IHNvcnRl"
        "ZCgocmUuZXNjYXBlKGEpIGZvciBhIGluIGFsaWFzZXMpLCBrZXk9bGVuLCByZXZlcnNlPVRydWUp"
        "CiAgICByZXR1cm4gcmUuY29tcGlsZShyIig/PCFbYS16MC05XSkoIiArICJ8Ii5qb2luKHBhcnRz"
        "KSArIHIiKSg/IVthLXowLTldKSIsIHJlLkkpCgoKRkxBVk9SX1JYID0ge2s6IF9wYXR0ZXJuKHYp"
        "IGZvciBrLCB2IGluIEZMQVZPUl9BTElBU0VTLml0ZW1zKCl9CkJSQU5EX1JYID0ge2s6IF9wYXR0"
        "ZXJuKHYpIGZvciBrLCB2IGluIEJSQU5EX0FMSUFTRVMuaXRlbXMoKX0KCgpkZWYgZXh0cmFjdCh0"
        "ZXh0KToKICAgICIiIi0+IChmbGF2b3JzLCBicmFuZHMsIG5vaXNlX3N0cmlwcGVkKS4gU2V0cywg"
        "bm90IGNvdW50czogb25lIGNvbW1lbnQKICAgIHNheWluZyAibWFuZ28gbWFuZ28gbWFuZ28iIGlz"
        "IG9uZSBwZXJzb24ncyBvcGluaW9uLCBub3QgdGhyZWUuIiIiCiAgICBpZiBub3QgdGV4dDoKICAg"
        "ICAgICByZXR1cm4gc2V0KCksIHNldCgpLCBGYWxzZQogICAgY2xlYW4sIG4gPSBOT0lTRS5zdWJu"
        "KCIgIiwgdGV4dCkKICAgIGJyYW5kcywgc3BhbnMgPSBzZXQoKSwgW10KICAgIGZvciBiLCByeCBp"
        "biBCUkFORF9SWC5pdGVtcygpOgogICAgICAgIG0gPSByeC5zZWFyY2goY2xlYW4pCiAgICAgICAg"
        "aWYgbToKICAgICAgICAgICAgYnJhbmRzLmFkZChiKQogICAgICAgICAgICBzcGFucy5leHRlbmQo"
        "KHguc3RhcnQoKSwgeC5lbmQoKSkgZm9yIHggaW4gcnguZmluZGl0ZXIoY2xlYW4pKQogICAgZmxh"
        "dm9ycyA9IHNldCgpCiAgICBmb3IgZiwgcnggaW4gRkxBVk9SX1JYLml0ZW1zKCk6CiAgICAgICAg"
        "bSA9IHJ4LnNlYXJjaChjbGVhbikKICAgICAgICBpZiBub3QgbToKICAgICAgICAgICAgY29udGlu"
        "dWUKICAgICAgICAjIFVuYW1iaWd1b3VzIGZsYXZvcnMgY291bnQgb24gc2lnaHQuIEFtYmlndW91"
        "cyBvbmVzIC0gdGVybXMgdGhhdCBhcmUKICAgICAgICAjIGFsc28gZHJpbmtzIG9yIGZvb2RzIGlu"
        "IHRoZWlyIG93biByaWdodCAtIG5lZWQgYSBtYXJrZXIgb3IgYSBicmFuZAogICAgICAgICMgd2l0"
        "aGluIENPTlRFWFRfV0lORE9XIGNoYXJhY3RlcnMuCiAgICAgICAgaWYgZiBpbiBBTUJJR1VPVVMg"
        "YW5kIG5vdCBhbnkoCiAgICAgICAgICAgICAgICBfbGljZW5zZWQoY2xlYW4sIHgsIHNwYW5zKSBm"
        "b3IgeCBpbiByeC5maW5kaXRlcihjbGVhbikpOgogICAgICAgICAgICBjb250aW51ZQogICAgICAg"
        "IGZsYXZvcnMuYWRkKGYpCiAgICByZXR1cm4gZmxhdm9ycywgYnJhbmRzLCBib29sKG4pCgoKZGVm"
        "IHRvX2ZhbWlseShmbGF2b3IpOgogICAgIiIiUm9sbCBhIG1hdGNoZWQgZmxhdm9yIHVwIHRvIHRo"
        "ZSBwcmUtcmVnaXN0ZXJlZCBmYW1pbHksIHVzaW5nIHRoZSBzYW1lCiAgICBmdW5jdGlvbiB0aGUg"
        "UERJIHNpZGUgdXNlcyAtIHNvIFJlZGRpdCBtZW50aW9uIHNoYXJlIGFuZCBQREkgdW5pdCBzaGFy"
        "ZSBhcmUKICAgIGJpbm5lZCBpZGVudGljYWxseSBhbmQgY2FuIGJlIGNvbXBhcmVkIGF0IGFsbC4i"
        "IiIKICAgIHJldHVybiBmbGF2b3JfZmFtaWx5KHsiRkxBVk9SIjogZmxhdm9yfSkKCgojIC0tLSBz"
        "ZW50aW1lbnQgLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tLS0tLS0KIyBWQURFUiB3aGVuIGF2YWlsYWJsZSwgZWxzZSB0aGUgbGV4aWNvbiBm"
        "YWxsYmFjayB0aGUgZGFzaGJvYXJkIGFnZ3JlZ2F0b3IKIyBhbHJlYWR5IHVzZXMsIHNvIHRoZSB0"
        "d28gYWdyZWUuIFR1bmVkIGZvciBzb2NpYWwgdGV4dDogaXQgaGFuZGxlcyBuZWdhdGlvbiwKIyBp"
        "bnRlbnNpZmllcnMgYW5kIGVtb2ppLCB3aGljaCBhIGJhZy1vZi13b3JkcyBsZXhpY29uIGRvZXMg"
        "bm90LgpkZWYgc2VudGltZW50X2ZuKCk6CiAgICB0cnk6CiAgICAgICAgZnJvbSB2YWRlclNlbnRp"
        "bWVudC52YWRlclNlbnRpbWVudCBpbXBvcnQgU2VudGltZW50SW50ZW5zaXR5QW5hbHl6ZXIKICAg"
        "ICAgICBhbiA9IFNlbnRpbWVudEludGVuc2l0eUFuYWx5emVyKCkKICAgICAgICByZXR1cm4gbGFt"
        "YmRhIHQ6IGFuLnBvbGFyaXR5X3Njb3Jlcyh0KVsiY29tcG91bmQiXSwgInZhZGVyIgogICAgZXhj"
        "ZXB0IEltcG9ydEVycm9yOgogICAgICAgIHBvcyA9IHNldCgibG92ZSBncmVhdCBiZXN0IGFtYXpp"
        "bmcgYXdlc29tZSBkZWxpY2lvdXMgcGVyZmVjdCBmaXJlICIKICAgICAgICAgICAgICAgICAgImZh"
        "dm9yaXRlIGdvb2QgYm9tYiBnb2F0ZWQgYmFuZ2VyIHNvbGlkIHJlZnJlc2hpbmciLnNwbGl0KCkp"
        "CiAgICAgICAgbmVnID0gc2V0KCJoYXRlIHdvcnN0IGF3ZnVsIGdyb3NzIGRpc2d1c3RpbmcgbmFz"
        "dHkgdGVycmlibGUgYmFkICIKICAgICAgICAgICAgICAgICAgInRyYXNoIG1pZCBibGFuZCBjaGVt"
        "aWNhbCBzeXJ1cHkgb3ZlcnJhdGVkIi5zcGxpdCgpKQoKICAgICAgICBkZWYgc2NvcmUodCk6CiAg"
        "ICAgICAgICAgIHcgPSByZS5maW5kYWxsKHIiW2EteiddKyIsICh0IG9yICIiKS5sb3dlcigpKQog"
        "ICAgICAgICAgICBwID0gc3VtKHggaW4gcG9zIGZvciB4IGluIHcpCiAgICAgICAgICAgIG4gPSBz"
        "dW0oeCBpbiBuZWcgZm9yIHggaW4gdykKICAgICAgICAgICAgcmV0dXJuIDAuMCBpZiBwICsgbiA9"
        "PSAwIGVsc2UgKHAgLSBuKSAvIChwICsgbikKICAgICAgICByZXR1cm4gc2NvcmUsICJsZXhpY29u"
        "LWZhbGxiYWNrIChwaXAgaW5zdGFsbCB2YWRlclNlbnRpbWVudCBmb3IgVkFERVIpIgoKCiMgImZh"
        "dm9yaXRlIiBtZW50aW9ucyAtIHRoZSBicmllZiBhc2tzIGZvciB0aGlzIHNlcGFyYXRlbHkgZnJv"
        "bSBwbGFpbiBtZW50aW9ucywKIyBhbmQgaXQgaXMgYSBtdWNoIHN0cm9uZ2VyIHNpZ25hbDogc29t"
        "ZW9uZSBuYW1pbmcgYSBmYXZvdXJpdGUgaXMgc3RhdGluZyBhCiMgcHJlZmVyZW5jZSwgbm90IGp1"
        "c3QgdXNpbmcgYSB3b3JkLgpGQVZPUklURSA9IHJlLmNvbXBpbGUoCiAgICByIlxiKGZhdm91P3Jp"
        "dGV8YmVzdCAoPzpmbGF2b3U/cnxvbmV8ZXZlcil8Z29bLSBdP3RvfCIKICAgIHIiaSBsb3ZlfG15"
        "IGZhdm91P3JpdGV8dG9wIHRpZXJ8c1stIF0/dGllcnxnb2F0ZWQpXGIiLCByZS5JKQoKCmRlZiBh"
        "bmFseXNlKHJvd3MsIHRleHRfa2V5PSJjb21tZW50IiwgZGF0ZV9rZXk9Tm9uZSwgbGltaXQ9Tm9u"
        "ZSk6CiAgICAiIiJTY29yZSBhbiBpdGVyYWJsZSBvZiBkaWN0IHJvd3MuIFJldHVybnMgYWdncmVn"
        "YXRlcyBvbmx5IC0gbmV2ZXIgdGV4dC4KCiAgICByb3dzOiBhbnkgaXRlcmFibGUgb2YgZGljdHMg"
        "d2l0aCBhIHRleHQgZmllbGQuIFdvcmtzIGZvciBSZWRkaXQgY29tbWVudHMsCiAgICBSZWRkaXQg"
        "cG9zdCB0aXRsZXMrc2VsZnRleHQsIGFuZCB0aGUgWW91VHViZSBjb3JwdXMgYWxpa2UuCiAgICAi"
        "IiIKICAgIHNjb3JlLCBlbmdpbmUgPSBzZW50aW1lbnRfZm4oKQogICAgZmwgPSBjb2xsZWN0aW9u"
        "cy5kZWZhdWx0ZGljdChsYW1iZGE6IHsibWVudGlvbnMiOiAwLCAiZmF2IjogMCwgInBvcyI6IDAs"
        "CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICJuZWciOiAwLCAibmV1"
        "IjogMCwgInNlbnRfc3VtIjogMC4wfSkKICAgIGJyID0gY29sbGVjdGlvbnMuZGVmYXVsdGRpY3Qo"
        "bGFtYmRhOiB7Im1lbnRpb25zIjogMCwgImZhdiI6IDAsICJwb3MiOiAwLAogICAgICAgICAgICAg"
        "ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAibmVnIjogMCwgIm5ldSI6IDAsICJzZW50X3N1"
        "bSI6IDAuMH0pCiAgICBzZWVuID0gbWF0Y2hlZCA9IG5vaXNlX2hpdHMgPSAwCgogICAgZm9yIHJv"
        "dyBpbiByb3dzOgogICAgICAgIGlmIGxpbWl0IGFuZCBzZWVuID49IGxpbWl0OgogICAgICAgICAg"
        "ICBicmVhawogICAgICAgIHNlZW4gKz0gMQogICAgICAgIHRleHQgPSByb3cuZ2V0KHRleHRfa2V5"
        "KSBvciAiIgogICAgICAgIGZsYXZvcnMsIGJyYW5kcywgaGFkX25vaXNlID0gZXh0cmFjdCh0ZXh0"
        "KQogICAgICAgIG5vaXNlX2hpdHMgKz0gaGFkX25vaXNlCiAgICAgICAgaWYgbm90IGZsYXZvcnMg"
        "YW5kIG5vdCBicmFuZHM6CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgbWF0Y2hlZCArPSAx"
        "CiAgICAgICAgcyA9IHNjb3JlKHRleHQpCiAgICAgICAgZmF2ID0gYm9vbChGQVZPUklURS5zZWFy"
        "Y2godGV4dCkpCiAgICAgICAgYnVja2V0ID0gInBvcyIgaWYgcyA+IDAuMDUgZWxzZSAibmVnIiBp"
        "ZiBzIDwgLTAuMDUgZWxzZSAibmV1IgogICAgICAgIGZvciB0YXJnZXQsIGtleXMgaW4gKChmbCwg"
        "Zmxhdm9ycyksIChiciwgYnJhbmRzKSk6CiAgICAgICAgICAgIGZvciBrIGluIGtleXM6CiAgICAg"
        "ICAgICAgICAgICBkID0gdGFyZ2V0W2tdCiAgICAgICAgICAgICAgICBkWyJtZW50aW9ucyJdICs9"
        "IDEKICAgICAgICAgICAgICAgIGRbImZhdiJdICs9IGZhdgogICAgICAgICAgICAgICAgZFtidWNr"
        "ZXRdICs9IDEKICAgICAgICAgICAgICAgIGRbInNlbnRfc3VtIl0gKz0gcwoKICAgIGRlZiBmaW5p"
        "c2goZCk6CiAgICAgICAgb3V0ID0gW10KICAgICAgICB0b3RhbCA9IHN1bSh2WyJtZW50aW9ucyJd"
        "IGZvciB2IGluIGQudmFsdWVzKCkpIG9yIDEKICAgICAgICBmb3IgaywgdiBpbiBzb3J0ZWQoZC5p"
        "dGVtcygpLCBrZXk9bGFtYmRhIGt2OiAta3ZbMV1bIm1lbnRpb25zIl0pOgogICAgICAgICAgICBv"
        "dXQuYXBwZW5kKHsKICAgICAgICAgICAgICAgICoqeyJuYW1lIjoga30sICoqdiwKICAgICAgICAg"
        "ICAgICAgICJtZW50aW9uX3NoYXJlX3BjdCI6IHJvdW5kKHZbIm1lbnRpb25zIl0gLyB0b3RhbCAq"
        "IDEwMCwgMiksCiAgICAgICAgICAgICAgICAiZmF2X3NoYXJlX3BjdCI6IHJvdW5kKHZbImZhdiJd"
        "IC8gdlsibWVudGlvbnMiXSAqIDEwMCwgMikgaWYgdlsibWVudGlvbnMiXSBlbHNlIDAsCiAgICAg"
        "ICAgICAgICAgICAjIE5ldCBzZW50aW1lbnQgYXMgKHBvcyAtIG5lZykgLyBtZW50aW9ucywgYm91"
        "bmRlZCAtMS4uMS4gVGhlIG1lYW4KICAgICAgICAgICAgICAgICMgY29tcG91bmQgc2NvcmUgaXMg"
        "cmVwb3J0ZWQgdG9vOyB0aGV5IGRpc2FncmVlIHdoZW4gYSBmbGF2b3IKICAgICAgICAgICAgICAg"
        "ICMgZHJhd3Mgc3Ryb25nIG9waW5pb25zIGluIGJvdGggZGlyZWN0aW9ucywgd2hpY2ggaXMgd29y"
        "dGggc2VlaW5nLgogICAgICAgICAgICAgICAgIm5ldF9zZW50aW1lbnQiOiByb3VuZCgodlsicG9z"
        "Il0gLSB2WyJuZWciXSkgLyB2WyJtZW50aW9ucyJdLCAzKSBpZiB2WyJtZW50aW9ucyJdIGVsc2Ug"
        "MCwKICAgICAgICAgICAgICAgICJtZWFuX2NvbXBvdW5kIjogcm91bmQodlsic2VudF9zdW0iXSAv"
        "IHZbIm1lbnRpb25zIl0sIDMpIGlmIHZbIm1lbnRpb25zIl0gZWxzZSAwLAogICAgICAgICAgICB9"
        "KQogICAgICAgIHJldHVybiBvdXQKCiAgICByZXR1cm4gewogICAgICAgICJlbmdpbmUiOiBlbmdp"
        "bmUsCiAgICAgICAgInJvd3Nfc2VlbiI6IHNlZW4sICJyb3dzX21hdGNoZWQiOiBtYXRjaGVkLAog"
        "ICAgICAgICJtYXRjaF9yYXRlX3BjdCI6IHJvdW5kKG1hdGNoZWQgLyBzZWVuICogMTAwLCAyKSBp"
        "ZiBzZWVuIGVsc2UgMCwKICAgICAgICAibm9pc2Vfc3RyaXBwZWQiOiBub2lzZV9oaXRzLAogICAg"
        "ICAgICJmbGF2b3JzIjogZmluaXNoKGZsKSwgImJyYW5kcyI6IGZpbmlzaChiciksCiAgICB9CgoK"
        "ZGVmIF9kZW1vKHBhdGgsIGxpbWl0KToKICAgIGNzdi5maWVsZF9zaXplX2xpbWl0KDEwICoqIDcp"
        "CiAgICB3aXRoIG9wZW4ocGF0aCwgZW5jb2Rpbmc9InV0Zi04IiwgZXJyb3JzPSJyZXBsYWNlIikg"
        "YXMgZmg6CiAgICAgICAgcmVzID0gYW5hbHlzZShjc3YuRGljdFJlYWRlcihmaCksIGxpbWl0PWxp"
        "bWl0KQogICAgcHJpbnQoZiJcbmVuZ2luZToge3Jlc1snZW5naW5lJ119IikKICAgIHByaW50KGYi"
        "cm93cyB7cmVzWydyb3dzX3NlZW4nXTosfSAgbWF0Y2hlZCB7cmVzWydyb3dzX21hdGNoZWQnXTos"
        "fSAiCiAgICAgICAgICBmIih7cmVzWydtYXRjaF9yYXRlX3BjdCddfSUpICBub2lzZSBzdHJpcHBl"
        "ZCBmcm9tIHtyZXNbJ25vaXNlX3N0cmlwcGVkJ106LH1cbiIpCiAgICBmb3IgbGFiZWwsIGtleSBp"
        "biAoKCJGTEFWT1IiLCAiZmxhdm9ycyIpLCAoIkJSQU5EIiwgImJyYW5kcyIpKToKICAgICAgICBw"
        "cmludChmIntsYWJlbDo8MTR9eydtZW50aW9ucyc6PjEwfXsnc2hhcmUlJzo+OH17J2ZhdiUnOj43"
        "fXsnbmV0Jzo+N317J21lYW4nOj43fSIpCiAgICAgICAgZm9yIHIgaW4gcmVzW2tleV1bOjE0XToK"
        "ICAgICAgICAgICAgcHJpbnQoZiIgIHtyWyduYW1lJ106PDEyfXtyWydtZW50aW9ucyddOj4xMCx9"
        "e3JbJ21lbnRpb25fc2hhcmVfcGN0J106Pjh9IgogICAgICAgICAgICAgICAgICBmIntyWydmYXZf"
        "c2hhcmVfcGN0J106Pjd9e3JbJ25ldF9zZW50aW1lbnQnXTo+N317clsnbWVhbl9jb21wb3VuZCdd"
        "Oj43fSIpCiAgICAgICAgcHJpbnQoKQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBh"
        "cCA9IGFyZ3BhcnNlLkFyZ3VtZW50UGFyc2VyKGRlc2NyaXB0aW9uPV9fZG9jX18uc3BsaXRsaW5l"
        "cygpWzBdKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLWRlbW8iLCBtZXRhdmFyPSJDU1YiLCBoZWxw"
        "PSJydW4gb3ZlciBhIGNvbW1pdHRlZCBjb3JwdXMgYW5kIHByaW50IikKICAgIGFwLmFkZF9hcmd1"
        "bWVudCgiLS1saW1pdCIsIHR5cGU9aW50LCBkZWZhdWx0PTQwMDAwKQogICAgYSA9IGFwLnBhcnNl"
        "X2FyZ3MoKQogICAgaWYgYS5kZW1vOgogICAgICAgIF9kZW1vKGEuZGVtbywgYS5saW1pdCkKICAg"
        "IGVsc2U6CiAgICAgICAgYXAucHJpbnRfaGVscCgpCg=="
    ),
    "reddit_collector": (
        "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiJSZWRkaXQgRGF0YSBBUEkgY29sbGVjdG9yIGZvciBm"
        "bGF2b3IgKyBicmFuZCBtZW50aW9ucy4gV29ya3N0cmVhbSAzLCBpdGVtIDIuCgogICAgcHl0aG9u"
        "IGNhcHN0b25lL2NvbGxlY3RvcnMvcmVkZGl0X2NvbGxlY3Rvci5weSAtLWRyeS1ydW4gICAgICMg"
        "cGxhbiBvbmx5LCBubyBjYWxscwogICAgcHl0aG9uIGNhcHN0b25lL2NvbGxlY3RvcnMvcmVkZGl0"
        "X2NvbGxlY3Rvci5weSAtLW1vbnRocyAyNCAgICMgcmVhbCBydW4sIG5lZWRzIGNyZWRzCgpPRkZJ"
        "Q0lBTCBBUEkgT05MWS4gVGhpcyBtYWtlcyBhdXRoZW50aWNhdGVkIGNhbGxzIHRvIG9hdXRoLnJl"
        "ZGRpdC5jb20uIEl0IGRvZXMKbm90IGZldGNoLCBwYXJzZSBvciByZW5kZXIgcmVkZGl0LmNvbSBI"
        "VE1MLCBkb2VzIG5vdCB1c2Ugb2xkLnJlZGRpdC5jb20sIGFuZApkb2VzIG5vdCByZXBsYXkgYnJv"
        "d3NlciBjb29raWVzIC0gYWxsIG9mIHdoaWNoIGFyZSB0aGUgdGhpbmdzIHRoZSBwcm9qZWN0J3MK"
        "Y29tcGxpYW5jZSBydWxlcyBydWxlIG91dC4gSWYgYSByZXF1ZXN0IGZhaWxzLCBpdCBmYWlsczsg"
        "dGhlcmUgaXMgbm8KdW5hdXRoZW50aWNhdGVkIGZhbGxiYWNrIHBhdGggYW55d2hlcmUgaW4gdGhp"
        "cyBmaWxlLCBieSBkZXNpZ24uCgpDUkVERU5USUFMUyBDT01FIEZST00gVEhFIEVOVklST05NRU5U"
        "LCBORVZFUiBGUk9NIFRISVMgRklMRQogICAgQ3JlYXRlIGEgKipzY3JpcHQqKiBhcHAgYXQgaHR0"
        "cHM6Ly93d3cucmVkZGl0LmNvbS9wcmVmcy9hcHBzLCB0aGVuOgogICAgICBleHBvcnQgUkVERElU"
        "X0NMSUVOVF9JRD0uLi4KICAgICAgZXhwb3J0IFJFRERJVF9DTElFTlRfU0VDUkVUPS4uLgogICAg"
        "ICBleHBvcnQgUkVERElUX1VTRVJfQUdFTlQ9InNjcmlwdDpib2d1cy1iYW5hbmEtY2Fwc3RvbmU6"
        "djEgKGJ5IC91Lzx5b3U+KSIKICAgIEEgZGVzY3JpcHRpdmUgVXNlci1BZ2VudCBpcyByZXF1aXJl"
        "ZCBieSBSZWRkaXQgYW5kIGEgZ2VuZXJpYyBvbmUgZ2V0cwogICAgcmF0ZS1saW1pdGVkIGhhcmRl"
        "ci4gTm8gdG9rZW4gaXMgd3JpdHRlbiB0byBkaXNrIG9yIGxvZ2dlZC4KCj4+PiBCRUZPUkUgVEhF"
        "IEZJUlNUIFJFQUwgUlVOLCBTRUUgY2Fwc3RvbmUvUkVERElUX0FQSV9URVJNUy5tZCA8PDwKICAg"
        "IFRoZSBwcm9qZWN0IGJyaWVmIG1ha2VzIGEgY3VycmVudCB0ZXJtcyBzdW1tYXJ5IGEgcHJlY29u"
        "ZGl0aW9uIG9mIHJ1bm5pbmcKICAgIHRoaXMuIFRoYXQgZmlsZSByZWNvcmRzIHdoYXQgbXVzdCBi"
        "ZSBjb25maXJtZWQgYW5kIHdoeSBpdCBjb3VsZCBub3QgYmUKICAgIGNvbmZpcm1lZCBmcm9tIHRo"
        "aXMgZW52aXJvbm1lbnQuIC0tZHJ5LXJ1biB3b3JrcyB3aXRob3V0IGl0OyBhIHJlYWwgcnVuIGlz"
        "CiAgICBDYWkncyBjYWxsIHRvIG1ha2Uga25vd2luZ2x5LgoKUFJJVkFDWSAtIEVORk9SQ0VEIEhF"
        "UkUsIE5PVCBCWSBDT05WRU5USU9OCiAgICBVc2VybmFtZXMgYXJlIG5ldmVyIHJlYWQgaW50byB0"
        "aGUgYWdncmVnYXRlIGFuZCByYXcgdGV4dCBpcyBuZXZlciB3cml0dGVuCiAgICB0byBkaXNrLiBU"
        "aGUgY29sbGVjdG9yIGhvbGRzIGEgY29tbWVudCBib2R5IG9ubHkgbG9uZyBlbm91Z2ggdG8gc2Nv"
        "cmUgaXQsCiAgICB0aGVuIGRpc2NhcmRzIGl0LiBUaGUgb3V0cHV0IGlzIGNvdW50cyBhbmQgc2Vu"
        "dGltZW50IHBlciBmbGF2b3IgYW5kIGJyYW5kLgogICAgVGhpcyBtYXRjaGVzIHRoZSBydWxlIHRo"
        "ZSByZXBvIGFscmVhZHkgZm9sbG93cyBmb3IgZGF0YS9yZWRkaXQvLgoKV0hBVCBJVCBDQU5OT1Qg"
        "RE8KICAgIFJlZGRpdCdzIGxpc3RpbmcgZW5kcG9pbnRzIGNhcCBhcm91bmQgMSwwMDAgaXRlbXMg"
        "cGVyIHF1ZXJ5LCBzbyB0aGlzIGNhbm5vdAogICAgZW51bWVyYXRlIGEgc3VicmVkZGl0J3MgaGlz"
        "dG9yeS4gSXQgaXNzdWVzIG9uZSBxdWVyeSBwZXIgKHRlcm0geCBtb250aCkKICAgIHNsaWNlIHRv"
        "IGdldCBkZWVwZXIgdGhhbiBhIHNpbmdsZSBzd2VlcCwgd2hpY2ggeWllbGRzIGEgQ09OU0lTVEVO"
        "VCBTQU1QTEUKICAgIHBlciBtb250aCAtIGdvb2QgZm9yIGRpcmVjdGlvbiBhbmQgcmVsYXRpdmUg"
        "bW92ZW1lbnQsIG5vdCBmb3IgYWJzb2x1dGUKICAgIGNvdW50cy4gQW55IGNoYXJ0IGJ1aWx0IG9u"
        "IGl0IG11c3Qgc2F5IHNvLgoiIiIKaW1wb3J0IGFyZ3BhcnNlCmltcG9ydCBjb2xsZWN0aW9ucwpp"
        "bXBvcnQgZGF0ZXRpbWUgYXMgZHQKaW1wb3J0IGpzb24KaW1wb3J0IG9zCmltcG9ydCBzeXMKaW1w"
        "b3J0IHRpbWUKaW1wb3J0IHVybGxpYi5wYXJzZQppbXBvcnQgdXJsbGliLnJlcXVlc3QKClJPT1Qg"
        "PSBvcy5wYXRoLmRpcm5hbWUob3MucGF0aC5kaXJuYW1lKG9zLnBhdGguZGlybmFtZShvcy5wYXRo"
        "LmFic3BhdGgoX19maWxlX18pKSkpCnN5cy5wYXRoLmluc2VydCgwLCBvcy5wYXRoLmRpcm5hbWUo"
        "b3MucGF0aC5hYnNwYXRoKF9fZmlsZV9fKSkpCmZyb20gZmxhdm9yX21lbnRpb25zIGltcG9ydCBh"
        "bmFseXNlLCBGTEFWT1JfQUxJQVNFUywgQlJBTkRfQUxJQVNFUyAgIyBub3FhOiBFNDAyCgojIC0t"
        "LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tIGNvbmZpZyAtLQpPVVRfRElSID0gb3MucGF0aC5qb2luKFJPT1QsICJkYXRhL3JlZGRp"
        "dCIpCkNBQ0hFX0RJUiA9IG9zLnBhdGguam9pbihST09ULCAiLmNhY2hlL3JlZGRpdCIpCmRlZiB1"
        "YSgpOgogICAgIiIiUmVhZCB0aGUgVXNlci1BZ2VudCBhdCBDQUxMIHRpbWUsIG5ldmVyIGF0IGlt"
        "cG9ydCB0aW1lLgoKICAgIFRoaXMgd2FzIGBVQSA9IG9zLmVudmlyb24uZ2V0KC4uLilgIGV2YWx1"
        "YXRlZCB3aGVuIHRoZSBtb2R1bGUgbG9hZGVkLCBhbmQKICAgIGl0IGJyb2tlIHRoZSBzdGFuZGFs"
        "b25lIGJ1bmRsZTogdGhlIGJ1bmRsZSBpbnN0YWxscyBpdHMgZW1iZWRkZWQgbW9kdWxlcwogICAg"
        "YmVmb3JlIG1haW4oKSBydW5zLCBzbyBVQSB3YXMgY2FwdHVyZWQgYXMgIiIgYmVmb3JlIGxvYWRf"
        "ZG90ZW52KCkgaGFkIHB1dAogICAgYW55dGhpbmcgaW4gdGhlIGVudmlyb25tZW50LiBUaGUgY3Jl"
        "ZGVudGlhbCBjaGVjayB0aGVuIGZhaWxlZCB3aXRoCiAgICAiTWlzc2luZyBjcmVkZW50aWFscyIg"
        "b24gYSBtYWNoaW5lIHdob3NlIC5lbnYgaGFkIGp1c3QgbG9hZGVkIHRocmVlCiAgICB2YXJpYWJs"
        "ZXMgc3VjY2Vzc2Z1bGx5IC0gcHJlZmxpZ2h0IHNhdyB0aGVtLCB0aGlzIGRpZCBub3QuCgogICAg"
        "QW55dGhpbmcgcmVhZCBmcm9tIHRoZSBlbnZpcm9ubWVudCBhdCBpbXBvcnQgdGltZSBoYXMgdGhl"
        "IHNhbWUgaGF6YXJkLgogICAgUmVhZCBpdCB3aGVuIHlvdSBuZWVkIGl0LiIiIgogICAgcmV0dXJu"
        "IG9zLmVudmlyb24uZ2V0KCJSRURESVRfVVNFUl9BR0VOVCIsICIiKS5zdHJpcCgpCgojIFN1YnJl"
        "ZGRpdCBuYW1lcyBhcmUgY2FzZS1pbnNlbnNpdGl2ZSBvbiBSZWRkaXQsIHNvICJlbmVyZ3lkcmlu"
        "a3MiIGFuZAojICJFbmVyZ3lEcmlua3MiIGFyZSBvbmUgc3VicmVkZGl0IGFuZCBsaXN0aW5nIGJv"
        "dGggYnVybmVkIGhhbGYgdGhlIGNhbGxzIG9uCiMgdGhvc2Ugcm93cyB0d2ljZS4gRGVkdXBlZCBj"
        "YXNlLWluc2Vuc2l0aXZlbHkgYmVsb3cgcmF0aGVyIHRoYW4gYnkgaGFuZCwgc28gYQojIGZ1dHVy"
        "ZSBlZGl0IGNhbm5vdCByZWludHJvZHVjZSBpdC4KX1NVQlMgPSBbIkVuZXJneURyaW5rcyIsICJj"
        "YWZmZWluZSIsICJDZWxzaXVzX09mZmljaWFsIiwgIk1vbnN0ZXJFbmVyZ3kiLAogICAgICAgICAi"
        "YmFuZ19lbmVyZ3kiLCAiQWxhbmlOdSIsICJHaG9zdEVuZXJneSJdClNVQlJFRERJVFMgPSBsaXN0"
        "KHtzLmxvd2VyKCk6IHMgZm9yIHMgaW4gX1NVQlN9LnZhbHVlcygpKQoKIyBQcmUtcmVnaXN0ZXJl"
        "ZCBzZWFyY2ggdGVybXMuIFByb3Bvc2VkLCBub3Qgc2V0dGxlZCAtIHRoZSBicmllZiBzYXlzIENh"
        "aQojIGFwcHJvdmVzIHRoZXNlIGJlZm9yZSBhIHJlYWwgcnVuLCBzbyB0aGV5IGxpdmUgaGVyZSB0"
        "byBiZSByZXZpZXdlZC4KU0VBUkNIX1RFUk1TID0gWyJlbmVyZ3kgZHJpbmsgZmxhdm9yIiwgImVu"
        "ZXJneSBkcmluayB0YXN0ZSIsICJiZXN0IGZsYXZvciIsCiAgICAgICAgICAgICAgICAid29yc3Qg"
        "Zmxhdm9yIiwgIm5ldyBmbGF2b3IiLCAiZmxhdm9yIHJldmlldyIsICJ0aWVyIGxpc3QiXQoKIyBS"
        "ZWRkaXQncyBkb2N1bWVudGVkIGZyZWUgdGllciBmb3IgYW4gT0F1dGggc2NyaXB0IGFwcCBpcyAx"
        "MDAgcXVlcmllcyBwZXIKIyBtaW51dGUgYXZlcmFnZWQgb3ZlciBhIDEwLW1pbnV0ZSB3aW5kb3cu"
        "IFRoaXMgcGFjZXMgd2VsbCB1bmRlciB0aGF0OiB0aGUKIyBjb2xsZWN0b3IgaXMgbm90IHRoZSBi"
        "b3R0bGVuZWNrIGluIGFueW9uZSdzIGRheSBhbmQgYmVpbmcgYSBnb29kIGNsaWVudCBpcwojIGNo"
        "ZWFwZXIgdGhhbiBiZWluZyByYXRlLWxpbWl0ZWQuIFZFUklGWSBUSElTIE5VTUJFUiBhZ2FpbnN0"
        "IGN1cnJlbnQgZG9jcyAtCiMgaXQgaXMgZXhhY3RseSB0aGUgc29ydCBvZiBmaWd1cmUgdGhhdCBj"
        "aGFuZ2VzIChzZWUgUkVERElUX0FQSV9URVJNUy5tZCkuClFQTV9CVURHRVQgPSA2MApTTEVFUCA9"
        "IDYwLjAgLyBRUE1fQlVER0VUCgpUT0tFTl9VUkwgPSAiaHR0cHM6Ly93d3cucmVkZGl0LmNvbS9h"
        "cGkvdjEvYWNjZXNzX3Rva2VuIgpBUEkgPSAiaHR0cHM6Ly9vYXV0aC5yZWRkaXQuY29tIgoKCmNs"
        "YXNzIFF1b3RhOgogICAgIiIiQ291bnRzIGNhbGxzIGFuZCByZWFkcyBSZWRkaXQncyBvd24gcmF0"
        "ZS1saW1pdCBoZWFkZXJzIGJhY2ssIHNvIHRoZQogICAgY29sbGVjdG9yIHJlcG9ydHMgd2hhdCB0"
        "aGUgc2VydmVyIHNhaWQgcmF0aGVyIHRoYW4gd2hhdCBpdCBhc3N1bWVkLiIiIgoKICAgIGRlZiBf"
        "X2luaXRfXyhzZWxmKToKICAgICAgICBzZWxmLmNhbGxzID0gMAogICAgICAgIHNlbGYucmVtYWlu"
        "aW5nID0gTm9uZQogICAgICAgIHNlbGYucmVzZXQgPSBOb25lCiAgICAgICAgc2VsZi5zdGFydGVk"
        "ID0gdGltZS50aW1lKCkKCiAgICBkZWYgbm90ZShzZWxmLCBoZWFkZXJzKToKICAgICAgICBzZWxm"
        "LmNhbGxzICs9IDEKICAgICAgICBmb3IgaywgYXR0ciBpbiAoKCJ4LXJhdGVsaW1pdC1yZW1haW5p"
        "bmciLCAicmVtYWluaW5nIiksCiAgICAgICAgICAgICAgICAgICAgICAgICgieC1yYXRlbGltaXQt"
        "cmVzZXQiLCAicmVzZXQiKSk6CiAgICAgICAgICAgIHYgPSBoZWFkZXJzLmdldChrKQogICAgICAg"
        "ICAgICBpZiB2IGlzIG5vdCBOb25lOgogICAgICAgICAgICAgICAgdHJ5OgogICAgICAgICAgICAg"
        "ICAgICAgIHNldGF0dHIoc2VsZiwgYXR0ciwgZmxvYXQodikpCiAgICAgICAgICAgICAgICBleGNl"
        "cHQgVmFsdWVFcnJvcjoKICAgICAgICAgICAgICAgICAgICBwYXNzCgogICAgZGVmIHJlcG9ydChz"
        "ZWxmKToKICAgICAgICBtaW5zID0gKHRpbWUudGltZSgpIC0gc2VsZi5zdGFydGVkKSAvIDYwIG9y"
        "IDFlLTkKICAgICAgICByZXR1cm4geyJjYWxscyI6IHNlbGYuY2FsbHMsICJjYWxsc19wZXJfbWlu"
        "Ijogcm91bmQoc2VsZi5jYWxscyAvIG1pbnMsIDEpLAogICAgICAgICAgICAgICAgInNlcnZlcl9y"
        "ZW1haW5pbmciOiBzZWxmLnJlbWFpbmluZywgInNlcnZlcl9yZXNldF9zIjogc2VsZi5yZXNldH0K"
        "CgojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tIGNvbGxlY3RvciAtLQpkZWYgdG9rZW4oKToKICAgICIiIk9BdXRoMiBjbGllbnQt"
        "Y3JlZGVudGlhbHMgZ3JhbnQuIFJhaXNlcyByYXRoZXIgdGhhbiBkZWdyYWRpbmc6IHRoZXJlIGlz"
        "CiAgICBkZWxpYmVyYXRlbHkgbm8gdW5hdXRoZW50aWNhdGVkIHBhdGggdG8gZmFsbCBiYWNrIHRv"
        "LiIiIgogICAgY2lkID0gb3MuZW52aXJvbi5nZXQoIlJFRERJVF9DTElFTlRfSUQiLCAiIikuc3Ry"
        "aXAoKQogICAgc2VjID0gb3MuZW52aXJvbi5nZXQoIlJFRERJVF9DTElFTlRfU0VDUkVUIiwgIiIp"
        "LnN0cmlwKCkKICAgIGlmIG5vdCAoY2lkIGFuZCBzZWMgYW5kIHVhKCkpOgogICAgICAgIHN5cy5l"
        "eGl0KAogICAgICAgICAgICAiTWlzc2luZyBjcmVkZW50aWFscy4gU2V0IGFsbCB0aHJlZSwgdGhl"
        "biByZXJ1bjpcbiIKICAgICAgICAgICAgIiAgZXhwb3J0IFJFRERJVF9DTElFTlRfSUQ9Li4uXG4i"
        "CiAgICAgICAgICAgICIgIGV4cG9ydCBSRURESVRfQ0xJRU5UX1NFQ1JFVD0uLi5cbiIKICAgICAg"
        "ICAgICAgJyAgZXhwb3J0IFJFRERJVF9VU0VSX0FHRU5UPSJzY3JpcHQ6Ym9ndXMtYmFuYW5hLWNh"
        "cHN0b25lOnYxIChieSAvdS88eW91PikiXG4nCiAgICAgICAgICAgICJDcmVhdGUgYSAqc2NyaXB0"
        "KiBhcHAgYXQgaHR0cHM6Ly93d3cucmVkZGl0LmNvbS9wcmVmcy9hcHBzIikKICAgIGRhdGEgPSB1"
        "cmxsaWIucGFyc2UudXJsZW5jb2RlKHsiZ3JhbnRfdHlwZSI6ICJjbGllbnRfY3JlZGVudGlhbHMi"
        "fSkuZW5jb2RlKCkKICAgIGltcG9ydCBiYXNlNjQKICAgIGF1dGggPSBiYXNlNjQuYjY0ZW5jb2Rl"
        "KGYie2NpZH06e3NlY30iLmVuY29kZSgpKS5kZWNvZGUoKQogICAgcmVxID0gdXJsbGliLnJlcXVl"
        "c3QuUmVxdWVzdChUT0tFTl9VUkwsIGRhdGE9ZGF0YSwgaGVhZGVycz17CiAgICAgICAgIkF1dGhv"
        "cml6YXRpb24iOiAiQmFzaWMgIiArIGF1dGgsICJVc2VyLUFnZW50IjogdWEoKX0pCiAgICB0cnk6"
        "CiAgICAgICAgd2l0aCB1cmxsaWIucmVxdWVzdC51cmxvcGVuKHJlcSwgdGltZW91dD0zMCkgYXMg"
        "cjoKICAgICAgICAgICAgcmV0dXJuIGpzb24ubG9hZChyKVsiYWNjZXNzX3Rva2VuIl0KICAgIGV4"
        "Y2VwdCB1cmxsaWIuZXJyb3IuSFRUUEVycm9yIGFzIGU6CiAgICAgICAgIyBSZWRkaXQgcHV0cyB0"
        "aGUgYWN0dWFsIHJlYXNvbiBpbiB0aGUgcmVzcG9uc2UgYm9keS4gUmFpc2luZyB0aGUgYmFyZQog"
        "ICAgICAgICMgSFRUUEVycm9yIHRocmV3IGF3YXkgdGhlIG9uZSBwaWVjZSBvZiBpbmZvcm1hdGlv"
        "biB0aGF0IGV4cGxhaW5zIHRoZQogICAgICAgICMgZmFpbHVyZSBhbmQgbGVmdCBhIHRyYWNlYmFj"
        "ayB0aGF0IHNheXMgb25seSAiNDAzOiBGb3JiaWRkZW4iLgogICAgICAgIGJvZHkgPSAiIgogICAg"
        "ICAgIHRyeToKICAgICAgICAgICAgYm9keSA9IGUucmVhZCgpLmRlY29kZSgidXRmLTgiLCAicmVw"
        "bGFjZSIpWzo2MDBdLnN0cmlwKCkKICAgICAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgICAg"
        "ICBwYXNzCiAgICAgICAgaGludCA9IHsKICAgICAgICAgICAgNDAxOiAiQ3JlZGVudGlhbHMgcmVq"
        "ZWN0ZWQuIFRoZSBjbGllbnQgaWQgb3Igc2VjcmV0IGlzIHdyb25nLCBvciB0aGUgIgogICAgICAg"
        "ICAgICAgICAgICJhcHAgaXMgbm90IHR5cGUgJ3NjcmlwdCcuIElmIHlvdSByZWdlbmVyYXRlZCB0"
        "aGUgc2VjcmV0LCBtYWtlICIKICAgICAgICAgICAgICAgICAic3VyZSAuZW52IGhhcyB0aGUgTkVX"
        "IG9uZS4iLAogICAgICAgICAgICA0MDM6ICJGb3JiaWRkZW4uIE1vc3Qgb2Z0ZW4gdGhlIFVzZXIt"
        "QWdlbnQ6IFJlZGRpdCBibG9ja3MgZ2VuZXJpYyBvciAiCiAgICAgICAgICAgICAgICAgIm1hbGZv"
        "cm1lZCBvbmVzLiBDaGVjayB5b3VycyBpcyBmaWxsZWQgaW4gLSBhIGxpdGVyYWwgJzx5b3U+JyAi"
        "CiAgICAgICAgICAgICAgICAgImxlZnQgaW4gdGhlIHRlbXBsYXRlIHdpbGwgZG8gaXQuIENhbiBh"
        "bHNvIG1lYW4gdGhlIHNlcGFyYXRlICIKICAgICAgICAgICAgICAgICAnInJlZ2lzdGVyIHRvIHVz"
        "ZSB0aGUgQVBJIiBzdGVwIG9uIHJlZGRpdC5jb20vcHJlZnMvYXBwcyBpcyAnCiAgICAgICAgICAg"
        "ICAgICAgIm5vdCBjb21wbGV0ZSwgb3IgdGhlIElQIGlzIGJsb2NrZWQgKHRyeSBvZmYgYSBWUE4p"
        "LiIsCiAgICAgICAgICAgIDQyOTogIlJhdGUgbGltaXRlZCBiZWZvcmUgZXZlbiBnZXR0aW5nIGEg"
        "dG9rZW4gLSB3YWl0IGEgZmV3IG1pbnV0ZXMuIiwKICAgICAgICB9LmdldChlLmNvZGUsICIiKQog"
        "ICAgICAgIHN5cy5leGl0KAogICAgICAgICAgICBmIlxuUmVkZGl0IHJlZnVzZWQgdGhlIHRva2Vu"
        "IHJlcXVlc3Q6IEhUVFAge2UuY29kZX0ge2UucmVhc29ufVxuIgogICAgICAgICAgICBmIiAgVXNl"
        "ci1BZ2VudCBzZW50OiB7dWEoKSFyfVxuIgogICAgICAgICAgICBmIiAgUmVkZGl0IHNhaWQ6IHti"
        "b2R5IG9yICcoZW1wdHkgcmVzcG9uc2UgYm9keSknfVxuIgogICAgICAgICAgICBmIiAge2hpbnR9"
        "XG4iCiAgICAgICAgICAgIGYiXG5SdW4gd2l0aCAtLWNoZWNrLWF1dGggZm9yIGEgZnVsbCBkaWFn"
        "bm9zaXMuXG4iKQoKCmRlZiBnZXQocGF0aCwgdG9rLCBxdW90YSwgKipwYXJhbXMpOgogICAgIiIi"
        "T25lIGF1dGhlbnRpY2F0ZWQgR0VULiBDYWNoZXMgYnkgVVJMIHNvIGEgcmUtcnVuIGNvc3RzIG5v"
        "dGhpbmcgYW5kIGFuCiAgICBpbnRlcnJ1cHRlZCBydW4gcmVzdW1lcyAtIHdoaWNoIG1hdHRlcnMg"
        "d2hlbiBhIGZ1bGwgcHVsbCBpcyB0aG91c2FuZHMgb2YKICAgIGNhbGxzIGFuZCBSZWRkaXQncyBs"
        "aXN0aW5ncyBzaGlmdCB1bmRlciB5b3UuIiIiCiAgICB1cmwgPSBmIntBUEl9e3BhdGh9P3t1cmxs"
        "aWIucGFyc2UudXJsZW5jb2RlKHBhcmFtcyl9IgogICAga2V5ID0gb3MucGF0aC5qb2luKENBQ0hF"
        "X0RJUiwgc3RyKGFicyhoYXNoKHVybCkpKSArICIuanNvbiIpCiAgICBpZiBvcy5wYXRoLmV4aXN0"
        "cyhrZXkpOgogICAgICAgIHdpdGggb3BlbihrZXkpIGFzIGZoOgogICAgICAgICAgICByZXR1cm4g"
        "anNvbi5sb2FkKGZoKQogICAgcmVxID0gdXJsbGliLnJlcXVlc3QuUmVxdWVzdCh1cmwsIGhlYWRl"
        "cnM9ewogICAgICAgICJBdXRob3JpemF0aW9uIjogIkJlYXJlciAiICsgdG9rLCAiVXNlci1BZ2Vu"
        "dCI6IHVhKCl9KQogICAgZm9yIGF0dGVtcHQgaW4gcmFuZ2UoNCk6CiAgICAgICAgdHJ5OgogICAg"
        "ICAgICAgICB3aXRoIHVybGxpYi5yZXF1ZXN0LnVybG9wZW4ocmVxLCB0aW1lb3V0PTQ1KSBhcyBy"
        "OgogICAgICAgICAgICAgICAgcXVvdGEubm90ZSh7ay5sb3dlcigpOiB2IGZvciBrLCB2IGluIHIu"
        "aGVhZGVycy5pdGVtcygpfSkKICAgICAgICAgICAgICAgIGJvZHkgPSBqc29uLmxvYWQocikKICAg"
        "ICAgICAgICAgb3MubWFrZWRpcnMoQ0FDSEVfRElSLCBleGlzdF9vaz1UcnVlKQogICAgICAgICAg"
        "ICB3aXRoIG9wZW4oa2V5LCAidyIpIGFzIGZoOgogICAgICAgICAgICAgICAganNvbi5kdW1wKGJv"
        "ZHksIGZoKQogICAgICAgICAgICB0aW1lLnNsZWVwKFNMRUVQKQogICAgICAgICAgICByZXR1cm4g"
        "Ym9keQogICAgICAgIGV4Y2VwdCB1cmxsaWIuZXJyb3IuSFRUUEVycm9yIGFzIGU6CiAgICAgICAg"
        "ICAgIGlmIGUuY29kZSA9PSA0Mjk6ICAgICAgICAgICAgICAjIHJhdGUgbGltaXRlZDogYmFjayBv"
        "ZmYgYW5kIHJldHJ5CiAgICAgICAgICAgICAgICB0aW1lLnNsZWVwKDIgKiogYXR0ZW1wdCAqIDUp"
        "CiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICBpZiBlLmNvZGUgaW4gKDQwMSwg"
        "NDAzKToKICAgICAgICAgICAgICAgIHN5cy5leGl0KGYiUmVkZGl0IHJlZnVzZWQgdGhlIHJlcXVl"
        "c3QgKHtlLmNvZGV9KS4gQ2hlY2sgdGhlICIKICAgICAgICAgICAgICAgICAgICAgICAgICJjcmVk"
        "ZW50aWFscyBhbmQgdGhhdCB0aGUgYXBwIHR5cGUgaXMgJ3NjcmlwdCcuIikKICAgICAgICAgICAg"
        "cmFpc2UKICAgICAgICBleGNlcHQgdXJsbGliLmVycm9yLlVSTEVycm9yIGFzIGU6CiAgICAgICAg"
        "ICAgIGlmIGF0dGVtcHQgPT0gMzoKICAgICAgICAgICAgICAgIHJhaXNlCiAgICAgICAgICAgIHRp"
        "bWUuc2xlZXAoMiAqKiBhdHRlbXB0ICogMikKICAgIHJldHVybiBOb25lCgoKIyAtLS0gZ2V0dGlu"
        "ZyBwYXN0IHRoZSAxLDAwMC1pdGVtIGxpc3RpbmcgY2FwIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tCiMKIyBSZWRkaXQgY2FwcyBBTlkgc2luZ2xlIGxpc3RpbmcgYXQgcm91Z2hseSAx"
        "LDAwMCBpdGVtcy4gUGFnaW5hdGluZyB3aXRoCiMgYGFmdGVyYCBwYXN0IHRoYXQgcmV0dXJucyBu"
        "b3RoaW5nIC0gaXQgaXMgYSBwcm9kdWN0IGxpbWl0LCBub3QgYSByYXRlIGxpbWl0LAojIGFuZCBu"
        "byBhbW91bnQgb2YgcGF0aWVuY2Ugb3IgcG9saXRlbmVzcyBnZXRzIGEgMSwwMDFzdCBpdGVtIG91"
        "dCBvZiBvbmUgcXVlcnkuCiMKIyBZb3UgZ2V0IHBhc3QgaXQgYnkgUEFSVElUSU9OSU5HIHRoZSBz"
        "cGFjZSBpbnRvIG1hbnkgc2VwYXJhdGUgbGlzdGluZ3MsIGVhY2gKIyB3aXRoIGl0cyBvd24gMSww"
        "MDAgY2FwLCBhbmQgdGFraW5nIHRoZSB1bmlvbi4gVGhhdCBpcyBvcmRpbmFyeSBkb2N1bWVudGVk"
        "IEFQSQojIHVzZSwgbm90IGV2YXNpb246IGV2ZXJ5IGNhbGwgaXMgYW4gYXV0aGVudGljYXRlZCwg"
        "cmF0ZS1saW1pdGVkIHJlcXVlc3QgdG8gYQojIHB1YmxpYyBlbmRwb2ludC4gV2hhdCBpdCBpcyBO"
        "T1QgaXMgYSBjZW5zdXMgLSBzZWUgdGhlIGhvbmVzdHkgbm90ZSBiZWxvdy4KIwojIFRocmVlIGF4"
        "ZXMsIG11bHRpcGx5aW5nIHRvZ2V0aGVyOgojCiMgICAxLiBRVUVSWSBURVJNLiBFYWNoIGRpc3Rp"
        "bmN0IGBxYCBpcyBpdHMgb3duIGxpc3Rpbmcgd2l0aCBpdHMgb3duIGNhcC4gVGhpcwojICAgICAg"
        "aXMgdGhlIGJpZ2dlc3QgbGV2ZXIsIGFuZCBpdCBpcyB3aHkgdGhlIHRlcm0gbGlzdCBiZWxvdyBp"
        "bmNsdWRlcyBibGFuZAojICAgICAgaGlnaC1mcmVxdWVuY3kgd29yZHMgYXMgd2VsbCBhcyB0b3Bp"
        "Y2FsIG9uZXM6ICJ0aGUiIGFuZCAiaXQiIHBhcnRpdGlvbgojICAgICAgdGhlIHN1YnJlZGRpdCBm"
        "YXIgbW9yZSBldmVubHkgdGhhbiAidGllciBsaXN0IiBkb2VzLgojICAgMi4gU09SVC4gbmV3IC8g"
        "dG9wIC8gcmVsZXZhbmNlIC8gY29tbWVudHMgc3VyZmFjZSBkaWZmZXJlbnQgc2xpY2VzIG9mIHRo"
        "ZQojICAgICAgc2FtZSByZXN1bHQgc2V0LCBzbyB0aGV5IG92ZXJsYXAgaGVhdmlseSBidXQgbm90"
        "IGNvbXBsZXRlbHkuCiMgICAzLiBUSU1FIFdJTkRPVy4gYHRgIHRha2VzIGFsbC95ZWFyL21vbnRo"
        "L3dlZWsvZGF5LiBFYWNoIGlzIGEgc2VwYXJhdGUgY2FwLAojICAgICAgYW5kIHRoZSBuYXJyb3cg"
        "b25lcyByZWFjaCBjb250ZW50IHRoZSBgYWxsYCBsaXN0aW5nIGhhcyBsb25nIGJ1cmllZC4KIwoj"
        "IFRoZW4gdGhlIHJlYWwgbXVsdGlwbGllcjogQ09NTUVOVCBUUkVFUy4gVGhlIGNhcCBhcHBsaWVz"
        "IHRvIHBvc3QgbGlzdGluZ3MuCiMgRWFjaCB1bmlxdWUgcG9zdCdzIGNvbW1lbnRzIGFyZSBhIHNl"
        "cGFyYXRlIGZldGNoLCBhbmQgdGFzdGUgdGFsayBsaXZlcyBpbiB0aGUKIyBjb21tZW50cyBhbnl3"
        "YXkuIEEgZmV3IHRob3VzYW5kIHBvc3RzIGF0IDEwLTQwIGNvbW1lbnRzIGVhY2ggaXMgd2hlcmUg"
        "dGhlCiMgY29ycHVzIGFjdHVhbGx5IGNvbWVzIGZyb20uCiMKIyBIT05FU1RZIE5PVEUsIHdoaWNo"
        "IGJlbG9uZ3MgaW4gdGhlIG1ldGhvZHMgc2VjdGlvbiB0b286IHRoZSB1bmlvbiBvZiBtYW55CiMg"
        "Y2FwcGVkIGxpc3RpbmdzIGlzIHN0aWxsIG5vdCB0aGUgc3VicmVkZGl0LiBSZWRkaXQncyBzZWFy"
        "Y2ggaW5kZXggZG9lcyBub3QKIyByZWxpYWJseSBzdXJmYWNlIHZlcnkgb2xkIG9yIGxvdy1lbmdh"
        "Z2VtZW50IHBvc3RzIGF0IGFsbCwgc28gY292ZXJhZ2UgZGVjYXlzCiMgd2l0aCBhZ2UgaW4gYSB3"
        "YXkgdGhpcyBjYW5ub3QgbWVhc3VyZSBmcm9tIHRoZSBpbnNpZGUuIFJlcG9ydCB3aGF0IHdhcwoj"
        "IGNvbGxlY3RlZCwgbmV2ZXIgaW1wbHkgY29tcGxldGVuZXNzLgoKREVFUF9URVJNUyA9IFsKICAg"
        "ICMgaGlnaC1mcmVxdWVuY3kgcGFydGl0aW9uZXJzIC0gdGhlc2UgZG8gdGhlIGhlYXZ5IGxpZnRp"
        "bmcKICAgICJ0aGUiLCAiaXQiLCAiYSIsICJhbmQiLCAiaXMiLCAibXkiLCAidGhpcyIsICJ5b3Ui"
        "LCAiYnV0IiwgIm5vdCIsCiAgICAjIHRvcGljYWwsIGZvciBwcmVjaXNpb24gb24gdGhlIGZsYXZv"
        "ciBxdWVzdGlvbgogICAgImZsYXZvciIsICJmbGF2b3VyIiwgInRhc3RlIiwgInRhc3RlcyIsICJi"
        "ZXN0IiwgIndvcnN0IiwgIm5ldyIsICJ0cmllZCIsCiAgICAicmV2aWV3IiwgInRpZXIgbGlzdCIs"
        "ICJmYXZvcml0ZSIsICJzdWdhciIsICJjYWZmZWluZSIsICJjYW4iLCAiZHJpbmsiLApdCkRFRVBf"
        "U09SVFMgPSBbIm5ldyIsICJ0b3AiLCAicmVsZXZhbmNlIiwgImNvbW1lbnRzIl0KREVFUF9XSU5E"
        "T1dTID0gWyJhbGwiLCAieWVhciIsICJtb250aCJdCgpQQUdFID0gMTAwICAgICAgICAgICMgbWF4"
        "IFJlZGRpdCByZXR1cm5zIHBlciBjYWxsCkxJU1RJTkdfQ0FQID0gMTAwMCAgIyBwZXItbGlzdGlu"
        "ZyBjZWlsaW5nOyBzdG9wIHBhZ2luYXRpbmcgd2hlbiByZWFjaGVkCgoKZGVmIF9saXN0aW5nKHBh"
        "dGgsIHRvaywgcXVvdGEsICoqcGFyYW1zKToKICAgICIiIlBhZ2luYXRlIG9uZSBsaXN0aW5nIHRv"
        "IGl0cyBjYXAsIHlpZWxkaW5nIHBvc3QgZGljdHMuCgogICAgU3RvcHMgb246IG5vIGNoaWxkcmVu"
        "LCBubyBgYWZ0ZXJgIGN1cnNvciwgb3IgTElTVElOR19DQVAgcmVhY2hlZC4gVGhlIGNhcAogICAg"
        "Y2hlY2sgaXMgd2hhdCBrZWVwcyB0aGlzIGZyb20gc3BlbmRpbmcgY2FsbHMgb24gcGFnZXMgUmVk"
        "ZGl0IHdpbGwgbm90CiAgICBzZXJ2ZS4iIiIKICAgIGFmdGVyLCBzZWVuID0gTm9uZSwgMAogICAg"
        "d2hpbGUgc2VlbiA8IExJU1RJTkdfQ0FQOgogICAgICAgIHAgPSBkaWN0KHBhcmFtcywgbGltaXQ9"
        "UEFHRSkKICAgICAgICBpZiBhZnRlcjoKICAgICAgICAgICAgcFsiYWZ0ZXIiXSA9IGFmdGVyCiAg"
        "ICAgICAgYm9keSA9IGdldChwYXRoLCB0b2ssIHF1b3RhLCAqKnApCiAgICAgICAgaWYgbm90IGJv"
        "ZHk6CiAgICAgICAgICAgIHJldHVybgogICAgICAgIGRhdGEgPSBib2R5LmdldCgiZGF0YSIsIHt9"
        "KQogICAgICAgIGtpZHMgPSBkYXRhLmdldCgiY2hpbGRyZW4iLCBbXSkKICAgICAgICBpZiBub3Qg"
        "a2lkczoKICAgICAgICAgICAgcmV0dXJuCiAgICAgICAgZm9yIGMgaW4ga2lkczoKICAgICAgICAg"
        "ICAgeWllbGQgYy5nZXQoImRhdGEiLCB7fSkKICAgICAgICBzZWVuICs9IGxlbihraWRzKQogICAg"
        "ICAgIGFmdGVyID0gZGF0YS5nZXQoImFmdGVyIikKICAgICAgICBpZiBub3QgYWZ0ZXI6CiAgICAg"
        "ICAgICAgIHJldHVybgoKCmRlZiBoYXJ2ZXN0KHRvaywgcXVvdGEsIG1vbnRocywgdmVyYm9zZT1U"
        "cnVlLCBkZWVwPUZhbHNlLCBtYXhfcG9zdHM9Tm9uZSk6CiAgICAiIiJXYWxrIHRoZSBwYXJ0aXRp"
        "b24gc3BhY2UsIHlpZWxkaW5nIChtb250aCwgdGV4dCkgLSBURVhUIE9OTFkuCgogICAgUG9zdCBp"
        "ZHMgYXJlIGhlbGQgaW4gbWVtb3J5IHRvIGRlZHVwbGljYXRlIGFuZCB0byBmZXRjaCBjb21tZW50"
        "IHRyZWVzLCBhbmQKICAgIGFyZSBuZXZlciB5aWVsZGVkLCB3cml0dGVuIG9yIGxvZ2dlZC4gVGhl"
        "IGNhbGxlciByZWNlaXZlcyBiYXJlIHN0cmluZ3MsIHNvCiAgICBubyB1c2VybmFtZSwgaWQgb3Ig"
        "cGVybWFsaW5rIGNhbiByZWFjaCB0aGUgYW5hbHlzZXIgb3IgdGhlIG91dHB1dC4KICAgICIiIgog"
        "ICAgc2luY2UgPSBkdC5kYXRldGltZS51dGNub3coKSAtIGR0LnRpbWVkZWx0YShkYXlzPTMwICog"
        "bW9udGhzKQogICAgdGVybXMgPSBERUVQX1RFUk1TIGlmIGRlZXAgZWxzZSBTRUFSQ0hfVEVSTVMK"
        "ICAgIHNvcnRzID0gREVFUF9TT1JUUyBpZiBkZWVwIGVsc2UgWyJuZXciXQogICAgd2luZG93cyA9"
        "IERFRVBfV0lORE9XUyBpZiBkZWVwIGVsc2UgWyJhbGwiXQoKICAgIHNlZW5faWRzID0gc2V0KCkg"
        "ICAgICAjIGRlZHVwZSBhY3Jvc3MgcGFydGl0aW9uczsgaW4tbWVtb3J5IG9ubHkKICAgIHN0YXRz"
        "ID0geyJxdWVyaWVzIjogMCwgInBvc3RzX3JhdyI6IDAsICJwb3N0c191bmlxdWUiOiAwLCAiY29t"
        "bWVudHMiOiAwLAogICAgICAgICAgICAgInRvb19vbGQiOiAwfQoKICAgIGZvciBzdWIgaW4gU1VC"
        "UkVERElUUzoKICAgICAgICBmb3IgdGVybSBpbiB0ZXJtczoKICAgICAgICAgICAgZm9yIHNvcnQg"
        "aW4gc29ydHM6CiAgICAgICAgICAgICAgICBmb3Igd2luIGluIHdpbmRvd3M6CiAgICAgICAgICAg"
        "ICAgICAgICAgaWYgbWF4X3Bvc3RzIGFuZCBsZW4oc2Vlbl9pZHMpID49IG1heF9wb3N0czoKICAg"
        "ICAgICAgICAgICAgICAgICAgICAgYnJlYWsKICAgICAgICAgICAgICAgICAgICBzdGF0c1sicXVl"
        "cmllcyJdICs9IDEKICAgICAgICAgICAgICAgICAgICBmb3IgZCBpbiBfbGlzdGluZyhmIi9yL3tz"
        "dWJ9L3NlYXJjaCIsIHRvaywgcXVvdGEsIHE9dGVybSwKICAgICAgICAgICAgICAgICAgICAgICAg"
        "ICAgICAgICAgICAgICByZXN0cmljdF9zcj0xLCBzb3J0PXNvcnQsIHQ9d2luKToKICAgICAgICAg"
        "ICAgICAgICAgICAgICAgc3RhdHNbInBvc3RzX3JhdyJdICs9IDEKICAgICAgICAgICAgICAgICAg"
        "ICAgICAgcGlkID0gZC5nZXQoImlkIikKICAgICAgICAgICAgICAgICAgICAgICAgaWYgbm90IHBp"
        "ZCBvciBwaWQgaW4gc2Vlbl9pZHM6CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBjb250aW51"
        "ZSAgICAgICAgICAjIHVuaW9uLCBub3Qgc3VtCiAgICAgICAgICAgICAgICAgICAgICAgIHNlZW5f"
        "aWRzLmFkZChwaWQpCiAgICAgICAgICAgICAgICAgICAgICAgIHN0YXRzWyJwb3N0c191bmlxdWUi"
        "XSArPSAxCiAgICAgICAgICAgICAgICAgICAgICAgIGNyZWF0ZWQgPSBkdC5kYXRldGltZS51dGNm"
        "cm9tdGltZXN0YW1wKGQuZ2V0KCJjcmVhdGVkX3V0YyIsIDApKQogICAgICAgICAgICAgICAgICAg"
        "ICAgICBpZiBjcmVhdGVkIDwgc2luY2U6CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBzdGF0"
        "c1sidG9vX29sZCJdICs9IDEKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAg"
        "ICAgICAgICAgICAgICAgICAgICAgIG1vbnRoID0gY3JlYXRlZC5zdHJmdGltZSgiJVktJW0iKQog"
        "ICAgICAgICAgICAgICAgICAgICAgICB0ZXh0ID0gIiAiLmpvaW4oZmlsdGVyKE5vbmUsIFtkLmdl"
        "dCgidGl0bGUiKSwgZC5nZXQoInNlbGZ0ZXh0IildKSkKICAgICAgICAgICAgICAgICAgICAgICAg"
        "aWYgdGV4dC5zdHJpcCgpOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgeWllbGQgbW9udGgs"
        "IHRleHQKCiAgICAgICAgICAgICAgICAgICAgICAgICMgVGhlIG11bHRpcGxpZXIuIENvbW1lbnQg"
        "dHJlZXMgYXJlIG5vdCBzdWJqZWN0IHRvIHRoZQogICAgICAgICAgICAgICAgICAgICAgICAjIHBv"
        "c3QtbGlzdGluZyBjYXAsIGFuZCB0aGlzIGlzIHdoZXJlIHRhc3RlIHRhbGsgaXMuCiAgICAgICAg"
        "ICAgICAgICAgICAgICAgIGNib2R5ID0gZ2V0KGYiL3Ive3N1Yn0vY29tbWVudHMve3BpZH0iLCB0"
        "b2ssIHF1b3RhLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBsaW1pdD01MDAs"
        "IGRlcHRoPTIsIHNvcnQ9InRvcCIpCiAgICAgICAgICAgICAgICAgICAgICAgIGlmIG5vdCBjYm9k"
        "eSBvciBsZW4oY2JvZHkpIDwgMjoKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGNvbnRpbnVl"
        "CiAgICAgICAgICAgICAgICAgICAgICAgIGZvciB0IGluIF93YWxrX2NvbW1lbnRzKGNib2R5WzFd"
        "LmdldCgiZGF0YSIsIHt9KS5nZXQoImNoaWxkcmVuIiwgW10pKToKICAgICAgICAgICAgICAgICAg"
        "ICAgICAgICAgIHN0YXRzWyJjb21tZW50cyJdICs9IDEKICAgICAgICAgICAgICAgICAgICAgICAg"
        "ICAgIHlpZWxkIG1vbnRoLCB0CiAgICAgICAgICAgICAgICAgICAgaWYgdmVyYm9zZToKICAgICAg"
        "ICAgICAgICAgICAgICAgICAgcHJpbnQoZiIgIHIve3N1Yn0gcT17dGVybSFyfSBzb3J0PXtzb3J0"
        "fSB0PXt3aW59IC0+ICIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgZiJ7c3RhdHNbJ3Bv"
        "c3RzX3VuaXF1ZSddOix9IHVuaXF1ZSBwb3N0cywgIgogICAgICAgICAgICAgICAgICAgICAgICAg"
        "ICAgICBmIntzdGF0c1snY29tbWVudHMnXTosfSBjb21tZW50cyIsIGZsdXNoPVRydWUpCiAgICBo"
        "YXJ2ZXN0LnN0YXRzID0gc3RhdHMKCgpkZWYgX3dhbGtfY29tbWVudHMoY2hpbGRyZW4sIGRlcHRo"
        "PTApOgogICAgIiIiWWllbGQgY29tbWVudCBib2RpZXMgZnJvbSBhIHRyZWUuIFNraXBzIGBtb3Jl"
        "YCBzdHVicyByYXRoZXIgdGhhbgogICAgZXhwYW5kaW5nIHRoZW06IGVhY2ggZXhwYW5zaW9uIGlz"
        "IGFub3RoZXIgY2FsbCwgYW5kIGF0IHRoaXMgY29ycHVzIHNpemUgdGhlCiAgICBtYXJnaW5hbCBj"
        "b21tZW50IGlzIG5vdCB3b3J0aCB0aGUgcXVvdGEuIFJlY29yZGVkIGFzIGEga25vd24gbGltaXRh"
        "dGlvbi4iIiIKICAgIGlmIGRlcHRoID4gNDoKICAgICAgICByZXR1cm4KICAgIGZvciBjIGluIGNo"
        "aWxkcmVuIG9yIFtdOgogICAgICAgIGlmIGMuZ2V0KCJraW5kIikgIT0gInQxIjoKICAgICAgICAg"
        "ICAgY29udGludWUgICAgICAgICAgICAgICAgICAgICAgIyBgbW9yZWAgc3R1YnMgYW5kIGFueXRo"
        "aW5nIG5vbi1jb21tZW50CiAgICAgICAgZCA9IGMuZ2V0KCJkYXRhIiwge30pCiAgICAgICAgYm9k"
        "eSA9IGQuZ2V0KCJib2R5IikKICAgICAgICBpZiBib2R5IGFuZCBib2R5IG5vdCBpbiAoIltkZWxl"
        "dGVkXSIsICJbcmVtb3ZlZF0iKToKICAgICAgICAgICAgeWllbGQgYm9keQogICAgICAgIHJlcGxp"
        "ZXMgPSBkLmdldCgicmVwbGllcyIpCiAgICAgICAgaWYgaXNpbnN0YW5jZShyZXBsaWVzLCBkaWN0"
        "KToKICAgICAgICAgICAgeWllbGQgZnJvbSBfd2Fsa19jb21tZW50cygKICAgICAgICAgICAgICAg"
        "IHJlcGxpZXMuZ2V0KCJkYXRhIiwge30pLmdldCgiY2hpbGRyZW4iLCBbXSksIGRlcHRoICsgMSkK"
        "CgojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tLSBhbmFseXNlciAtLQpkZWYgcnVuKG1vbnRocywgbGltaXQ9Tm9uZSwgdmVyYm9z"
        "ZT1UcnVlLCBkZWVwPUZhbHNlLCBtYXhfcG9zdHM9Tm9uZSk6CiAgICBxdW90YSA9IFF1b3RhKCkK"
        "ICAgIHRvayA9IHRva2VuKCkKICAgIHJvd3MsIGJ5X21vbnRoID0gW10sIGNvbGxlY3Rpb25zLkNv"
        "dW50ZXIoKQogICAgZm9yIG1vbnRoLCB0ZXh0IGluIGhhcnZlc3QodG9rLCBxdW90YSwgbW9udGhz"
        "LCB2ZXJib3NlLCBkZWVwLCBtYXhfcG9zdHMpOgogICAgICAgIHJvd3MuYXBwZW5kKHsiY29tbWVu"
        "dCI6IHRleHQsICJtb250aCI6IG1vbnRofSkKICAgICAgICBieV9tb250aFttb250aF0gKz0gMQog"
        "ICAgICAgIGlmIGxpbWl0IGFuZCBsZW4ocm93cykgPj0gbGltaXQ6CiAgICAgICAgICAgIGJyZWFr"
        "CiAgICByZXMgPSBhbmFseXNlKHJvd3MpICAgICAgICAgICAgICAgICAgICAgICMgYWdncmVnYXRl"
        "cyBvbmx5CiAgICByZXNbIm1vbnRocyJdID0gZGljdChzb3J0ZWQoYnlfbW9udGguaXRlbXMoKSkp"
        "CiAgICByZXNbInF1b3RhIl0gPSBxdW90YS5yZXBvcnQoKQogICAgcmVzWyJoYXJ2ZXN0Il0gPSBn"
        "ZXRhdHRyKGhhcnZlc3QsICJzdGF0cyIsIHt9KQogICAgcmV0dXJuIHJlcwoKCmRlZiBfc2hvdyhw"
        "YXRoKToKICAgICIiIkRpc3BsYXkgcGF0aDogcmVsYXRpdmUgd2hlbiB0aGF0IGlzIGdlbnVpbmVs"
        "eSBzaG9ydGVyIGFuZCBpbnNpZGUgUk9PVCwKICAgIGFic29sdXRlIG90aGVyd2lzZS4gcmVscGF0"
        "aCBhZ2FpbnN0IFJPT1QgcHJvZHVjZWQgInZhci9mb2xkZXJzLy4uLiIgZm9yIGEKICAgIHRlbXAg"
        "ZGlyIG9uIG1hY09TIC0gYSBwYXRoIHRoYXQgZG9lcyBub3QgZXhpc3QgYW5kIGNhbm5vdCBiZSBj"
        "b3BpZWQuIiIiCiAgICB0cnk6CiAgICAgICAgcmVsID0gb3MucGF0aC5yZWxwYXRoKHBhdGgsIFJP"
        "T1QpCiAgICBleGNlcHQgVmFsdWVFcnJvcjoKICAgICAgICByZXR1cm4gcGF0aAogICAgcmV0dXJu"
        "IHBhdGggaWYgcmVsLnN0YXJ0c3dpdGgoIi4uIikgb3Igb3MucGF0aC5pc2FicyhyZWwpIGVsc2Ug"
        "cmVsCgoKZGVmIHdyaXRlKHJlcywgbW9udGhzKToKICAgIG9zLm1ha2VkaXJzKE9VVF9ESVIsIGV4"
        "aXN0X29rPVRydWUpCiAgICBzdGFtcCA9IGR0LmRhdGUudG9kYXkoKS5pc29mb3JtYXQoKQoKICAg"
        "IGZvciBuYW1lLCBrZXkgaW4gKCgiZmxhdm9yIiwgImZsYXZvcnMiKSwgKCJicmFuZCIsICJicmFu"
        "ZHMiKSk6CiAgICAgICAgcGF0aCA9IG9zLnBhdGguam9pbihPVVRfRElSLCBmIntuYW1lfV9wdWxz"
        "ZV9hcGlfe3N0YW1wfS5jc3YiKQogICAgICAgIGltcG9ydCBjc3YgYXMgX2NzdgogICAgICAgIHdp"
        "dGggb3BlbihwYXRoLCAidyIsIG5ld2xpbmU9IiIsIGVuY29kaW5nPSJ1dGYtOCIpIGFzIGZoOgog"
        "ICAgICAgICAgICB3ID0gX2Nzdi5EaWN0V3JpdGVyKGZoLCBmaWVsZG5hbWVzPWxpc3QocmVzW2tl"
        "eV1bMF0ua2V5cygpKSkKICAgICAgICAgICAgdy53cml0ZWhlYWRlcigpCiAgICAgICAgICAgIHcu"
        "d3JpdGVyb3dzKHJlc1trZXldKQogICAgICAgIHByaW50KGYiICB3cm90ZSB7X3Nob3cocGF0aCl9"
        "ICAoe2xlbihyZXNba2V5XSl9IHJvd3MpIikKCiAgICBtZXRhID0gb3MucGF0aC5qb2luKE9VVF9E"
        "SVIsIGYibWV0YV9hcGlfe3N0YW1wfS5jc3YiKQogICAgaW1wb3J0IGNzdiBhcyBfY3N2CiAgICB3"
        "aXRoIG9wZW4obWV0YSwgInciLCBuZXdsaW5lPSIiLCBlbmNvZGluZz0idXRmLTgiKSBhcyBmaDoK"
        "ICAgICAgICB3ID0gX2Nzdi53cml0ZXIoZmgpCiAgICAgICAgdy53cml0ZXJvdyhbImtleSIsICJ2"
        "YWx1ZSJdKQogICAgICAgIGZvciBrLCB2IGluIFsKICAgICAgICAgICAgKCJzb3VyY2UiLCAiUmVk"
        "ZGl0IERhdGEgQVBJIChvYXV0aC5yZWRkaXQuY29tKSIpLAogICAgICAgICAgICAoIm1ldGhvZCIs"
        "ICJhdXRoZW50aWNhdGVkIE9BdXRoIHNjcmlwdCBhcHA7IG5vIEhUTUwsIG5vIGNvb2tpZXMiKSwK"
        "ICAgICAgICAgICAgKCJzdWJyZWRkaXRzIiwgInwiLmpvaW4oU1VCUkVERElUUykpLAogICAgICAg"
        "ICAgICAoInNlYXJjaF90ZXJtcyIsICJ8Ii5qb2luKFNFQVJDSF9URVJNUykpLAogICAgICAgICAg"
        "ICAoIm1vbnRoc19yZXF1ZXN0ZWQiLCBtb250aHMpLAogICAgICAgICAgICAoInJvd3Nfc2VlbiIs"
        "IHJlc1sicm93c19zZWVuIl0pLAogICAgICAgICAgICAoInJvd3NfbWF0Y2hlZCIsIHJlc1sicm93"
        "c19tYXRjaGVkIl0pLAogICAgICAgICAgICAoIm1hdGNoX3JhdGVfcGN0IiwgcmVzWyJtYXRjaF9y"
        "YXRlX3BjdCJdKSwKICAgICAgICAgICAgKCJzZW50aW1lbnRfZW5naW5lIiwgcmVzWyJlbmdpbmUi"
        "XSksCiAgICAgICAgICAgICgiYXBpX2NhbGxzIiwgcmVzWyJxdW90YSJdWyJjYWxscyJdKSwKICAg"
        "ICAgICAgICAgKCJnZW5lcmF0ZWRfYXQiLCBkdC5kYXRldGltZS51dGNub3coKS5pc29mb3JtYXQo"
        "KSArICJaIiksCiAgICAgICAgICAgICgicHJpdmFjeSIsICJhZ2dyZWdhdGVzIG9ubHk7IG5vIHVz"
        "ZXJuYW1lcywgaWRzIG9yIHJhdyB0ZXh0IHN0b3JlZCIpLAogICAgICAgICAgICAoInNhbXBsaW5n"
        "IiwgImxpc3RpbmcgZW5kcG9pbnRzIGNhcCB+MTAwMCBpdGVtcy9xdWVyeTsgY29uc2lzdGVudCAi"
        "CiAgICAgICAgICAgICAgICAgICAgICAgICAic2FtcGxlIHBlciBtb250aCwgTk9UIGEgY2Vuc3Vz"
        "IiksCiAgICAgICAgXToKICAgICAgICAgICAgdy53cml0ZXJvdyhbaywgdl0pCiAgICBwcmludChm"
        "IiAgd3JvdGUge19zaG93KG1ldGEpfSIpCgoKIyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tIG1haW4gLS0KZGVmIHBsYW4o"
        "ZGVlcD1GYWxzZSk6CiAgICAiIiJXaGF0IGEgcmVhbCBydW4gd291bGQgZG8sIHByaW50ZWQgd2l0"
        "aG91dCBtYWtpbmcgYSBzaW5nbGUgY2FsbC4iIiIKICAgIHRlcm1zID0gREVFUF9URVJNUyBpZiBk"
        "ZWVwIGVsc2UgU0VBUkNIX1RFUk1TCiAgICBzb3J0cyA9IERFRVBfU09SVFMgaWYgZGVlcCBlbHNl"
        "IFsibmV3Il0KICAgIHdpbnMgPSBERUVQX1dJTkRPV1MgaWYgZGVlcCBlbHNlIFsiYWxsIl0KICAg"
        "IHBhcnRzID0gbGVuKFNVQlJFRERJVFMpICogbGVuKHRlcm1zKSAqIGxlbihzb3J0cykgKiBsZW4o"
        "d2lucykKICAgIGNhbGxzID0gcGFydHMKICAgIHByaW50KGYiIiIKUExBTiDigJQgbm8gbmV0d29y"
        "ayBjYWxscyBtYWRlICAgW3snREVFUCcgaWYgZGVlcCBlbHNlICdzdGFuZGFyZCd9XQoKICBzdWJy"
        "ZWRkaXRzICAgICB7bGVuKFNVQlJFRERJVFMpfSAgeycsICcuam9pbignci8nICsgeCBmb3IgeCBp"
        "biBTVUJSRURESVRTKX0KICBxdWVyeSB0ZXJtcyAgICB7bGVuKHRlcm1zKX0KICBzb3J0cyAgICAg"
        "ICAgICB7bGVuKHNvcnRzKX0gIHtzb3J0c30KICB0aW1lIHdpbmRvd3MgICB7bGVuKHdpbnMpfSAg"
        "e3dpbnN9CiAgLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tLS0tLS0tLS0tCiAgcGFydGl0aW9ucyAgICAge3BhcnRzOix9ICAoc3VicmVkZGl0"
        "IHggdGVybSB4IHNvcnQgeCB3aW5kb3cpCiAgZWFjaCBwYWdpbmF0ZXMgdG8gdGhlIHtMSVNUSU5H"
        "X0NBUDosfS1pdGVtIHBlci1saXN0aW5nIGNhcCwgc28gdGhlIGNlaWxpbmcgaXMKICB7cGFydHMg"
        "KiBMSVNUSU5HX0NBUDosfSBwb3N0LWhpdHMgYmVmb3JlIGRlZHVwZSAtIHRoZSB1bmlvbiB3aWxs"
        "IGJlIGZhciBzbWFsbGVyLAogIGFuZCB0aGF0IHVuaW9uIGlzIHRoZSBudW1iZXIgdGhhdCBtYXR0"
        "ZXJzLgoKICBzZWFyY2ggY2FsbHMgICB7cGFydHM6LH0gLi4ge3BhcnRzICogKExJU1RJTkdfQ0FQ"
        "IC8vIFBBR0UpOix9ICAoMSBwZXIgcGFnZSwgdXAgdG8ge0xJU1RJTkdfQ0FQIC8vIFBBR0V9IHBh"
        "Z2VzIGVhY2gpCiAgY29tbWVudCBjYWxscyAgMSBwZXIgVU5JUVVFIHBvc3QKICBwYWNpbmcgICAg"
        "ICAgICB7UVBNX0JVREdFVH0gcXVlcmllcy9taW4gKHtTTEVFUDouMWZ9cyBhcGFydCkKCiAgSE9X"
        "IFRIRSAxLDAwMCBDQVAgSVMgQkVBVEVOCiAgVGhlIGNhcCBpcyBwZXIgbGlzdGluZywgbm90IHBl"
        "ciBzdWJyZWRkaXQuIEVhY2ggZGlzdGluY3QgKHRlcm0sIHNvcnQsIHdpbmRvdykKICBpcyBpdHMg"
        "b3duIGxpc3Rpbmcgd2l0aCBpdHMgb3duIHtMSVNUSU5HX0NBUDosfS4gVGFraW5nIHRoZSB1bmlv"
        "biBhY3Jvc3Mge3BhcnRzOix9IG9mCiAgdGhlbSBpcyBvcmRpbmFyeSBBUEkgdXNlIC0gZXZlcnkg"
        "Y2FsbCBpcyBhdXRoZW50aWNhdGVkIGFuZCByYXRlLWxpbWl0ZWQuCiAgQ29tbWVudCB0cmVlcyBh"
        "cmUgbm90IHN1YmplY3QgdG8gdGhlIHBvc3QgY2FwIGF0IGFsbCwgYW5kIGFyZSB3aGVyZSBtb3N0"
        "IG9mCiAgdGhlIHRleHQgY29tZXMgZnJvbS4KCiAgV0hBVCBJVCBTVElMTCBJUyBOT1QKICBBIGNl"
        "bnN1cy4gUmVkZGl0J3Mgc2VhcmNoIGluZGV4IGRvZXMgbm90IHJlbGlhYmx5IHN1cmZhY2UgdmVy"
        "eSBvbGQgb3IKICBsb3ctZW5nYWdlbWVudCBwb3N0cywgc28gY292ZXJhZ2UgZGVjYXlzIHdpdGgg"
        "YWdlIGluIGEgd2F5IHRoaXMgY2Fubm90CiAgbWVhc3VyZSBmcm9tIHRoZSBpbnNpZGUuIFJlcG9y"
        "dCB3aGF0IHdhcyBjb2xsZWN0ZWQ7IG5ldmVyIGltcGx5IGNvbXBsZXRlbmVzcy4KCiAgV0hBVCBJ"
        "VCBDT1NUUyBJTiBUSU1FCiAgUGFjaW5nIGlzIHRoZSBiaW5kaW5nIGNvbnN0cmFpbnQsIG5vdCBx"
        "dW90YS4gQSBtb2NrIHJ1biBvZiB0aGUgc2FtZSBsb2dpYwogIChjYXBzdG9uZS90ZXN0cy90ZXN0"
        "X2RlZXBfaGFydmVzdC5weSkgdHVybmVkIDQ4IHBhcnRpdGlvbnMgaW50byB+MjEsNzAwCiAgdW5p"
        "cXVlIHBvc3RzLCBzbyB0aGlzIHBsYW4ncyB7cGFydHM6LH0gcGFydGl0aW9ucyBhcmUgaW4gdGhl"
        "IHRlbnMgb2YKICB0aG91c2FuZHMgb2YgcG9zdHMgLSBhbmQgZXZlcnkgdW5pcXVlIHBvc3QgY29z"
        "dHMgb25lIG1vcmUgY2FsbCBmb3IgaXRzCiAgY29tbWVudHMuIEF0IHtRUE1fQlVER0VUfS9taW4g"
        "dGhhdCBpcyByZWFsaXN0aWNhbGx5CiAgeyhwYXJ0cyArIDIwMDAwKSAqIFNMRUVQIC8gMzYwMDou"
        "MGZ9LXsocGFydHMgKiA1ICsgNDAwMDApICogU0xFRVAgLyAzNjAwOi4wZn0gSE9VUlMgZm9yIGEg"
        "ZnVsbCBwdWxsLgoKICBEbyBhIGJvdW5kZWQgZmlyc3QgcnVuIGluc3RlYWQsIGxvb2sgYXQgd2hh"
        "dCBjb21lcyBiYWNrLCB0aGVuIHdpZGVuOgogICAgICAtLWRlZXAgLS1tYXgtcG9zdHMgMjAwMCAg"
        "ICAgICAgKH57KDIwMCArIDIwMDApICogU0xFRVAgLyA2MDouMGZ9IG1pbikKICBUaGUgY2FjaGUg"
        "bWFrZXMgdGhpcyBmcmVlIHRvIHJlc3VtZSwgc28gYSBsb25nIHJ1biBjYW4gYmUgc3RvcHBlZCBh"
        "bmQKICByZXN0YXJ0ZWQgd2l0aG91dCBsb3Npbmcgd29yay4KCiAgY2FjaGUgICAgICAgICAge29z"
        "LnBhdGgucmVscGF0aChDQUNIRV9ESVIsIFJPT1QpfSAgKHJlLXJ1bnMgZnJlZSwgaW50ZXJydXB0"
        "ZWQgcnVucyByZXN1bWUpCiAgdm9jYWJ1bGFyeSAgICAge2xlbihGTEFWT1JfQUxJQVNFUyl9IGZs"
        "YXZvcnMgLyB7bGVuKEJSQU5EX0FMSUFTRVMpfSBicmFuZHMKICB3cml0ZXMgICAgICAgICBkYXRh"
        "L3JlZGRpdC9mbGF2b3JfcHVsc2VfYXBpXzxkYXRlPi5jc3YsIGJyYW5kXy4uLiwgbWV0YV8uLi4K"
        "ICBuZXZlciB3cml0ZXMgICB1c2VybmFtZXMsIHBvc3QgaWRzLCBwZXJtYWxpbmtzLCBvciByYXcg"
        "Y29tbWVudCB0ZXh0CgpDUkVERU5USUFMUyAgeydwcmVzZW50JyBpZiBvcy5lbnZpcm9uLmdldCgn"
        "UkVERElUX0NMSUVOVF9JRCcpIGVsc2UgJ05PVCBTRVQg4oCUIGEgcmVhbCBydW4gd2lsbCBzdG9w"
        "IGFuZCB0ZWxsIHlvdSBob3cnfQpURVJNUyAgICAgICAgcmVhZCBjYXBzdG9uZS9SRURESVRfQVBJ"
        "X1RFUk1TLm1kIGJlZm9yZSB0aGUgZmlyc3QgcmVhbCBydW4KIiIiKQoKCmRlZiBtYWluKCk6CiAg"
        "ICBhcCA9IGFyZ3BhcnNlLkFyZ3VtZW50UGFyc2VyKGRlc2NyaXB0aW9uPV9fZG9jX18uc3BsaXRs"
        "aW5lcygpWzBdKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLWRyeS1ydW4iLCBhY3Rpb249InN0b3Jl"
        "X3RydWUiLCBoZWxwPSJwcmludCB0aGUgcGxhbiwgY2FsbCBub3RoaW5nIikKICAgIGFwLmFkZF9h"
        "cmd1bWVudCgiLS1tb250aHMiLCB0eXBlPWludCwgZGVmYXVsdD0yNCwgaGVscD0iaG93IGZhciBi"
        "YWNrIChkZWZhdWx0IDI0KSIpCiAgICBhcC5hZGRfYXJndW1lbnQoIi0tbGltaXQiLCB0eXBlPWlu"
        "dCwgaGVscD0ic3RvcCBhZnRlciBOIHRleHRzIChmb3IgYSBjaGVhcCBmaXJzdCBsb29rKSIpCiAg"
        "ICBhcC5hZGRfYXJndW1lbnQoIi0tZGVlcCIsIGFjdGlvbj0ic3RvcmVfdHJ1ZSIsCiAgICAgICAg"
        "ICAgICAgICAgICAgaGVscD0icGFydGl0aW9uIGFjcm9zcyB0ZXJtcyB4IHNvcnRzIHggdGltZSB3"
        "aW5kb3dzIHRvIGdldCAiCiAgICAgICAgICAgICAgICAgICAgICAgICAicGFzdCB0aGUgMSwwMDAt"
        "aXRlbSBwZXItbGlzdGluZyBjYXAiKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLW1heC1wb3N0cyIs"
        "IHR5cGU9aW50LAogICAgICAgICAgICAgICAgICAgIGhlbHA9InN0b3Agb25jZSB0aGlzIG1hbnkg"
        "VU5JUVVFIHBvc3RzIGhhdmUgYmVlbiBzZWVuIikKICAgIGFwLmFkZF9hcmd1bWVudCgiLS1xdWll"
        "dCIsIGFjdGlvbj0ic3RvcmVfdHJ1ZSIpCiAgICBhID0gYXAucGFyc2VfYXJncygpCgogICAgaWYg"
        "YS5kcnlfcnVuOgogICAgICAgIHBsYW4oYS5kZWVwKQogICAgICAgIHJldHVybgoKICAgIHJlcyA9"
        "IHJ1bihhLm1vbnRocywgYS5saW1pdCwgdmVyYm9zZT1ub3QgYS5xdWlldCwgZGVlcD1hLmRlZXAs"
        "CiAgICAgICAgICAgICAgbWF4X3Bvc3RzPWEubWF4X3Bvc3RzKQogICAgaCA9IHJlcy5nZXQoImhh"
        "cnZlc3QiLCB7fSkKICAgIHByaW50KGYiXG4gIHtyZXNbJ3Jvd3Nfc2VlbiddOix9IHRleHRzLCB7"
        "cmVzWydyb3dzX21hdGNoZWQnXTosfSBtYXRjaGVkICIKICAgICAgICAgIGYiKHtyZXNbJ21hdGNo"
        "X3JhdGVfcGN0J119JSkgIMK3ICB7cmVzWydxdW90YSddWydjYWxscyddfSBBUEkgY2FsbHMiKQog"
        "ICAgaWYgaDoKICAgICAgICAjIFByaW50ZWQgYmVjYXVzZSBpdCBpcyB0aGUgbnVtYmVyIHRoYXQg"
        "YW5zd2VycyAiZGlkIHdlIGdldCBwYXN0IDEsMDAwIjoKICAgICAgICAjIHBvc3RzX3JhdyBjb3Vu"
        "dHMgZXZlcnkgaGl0IGFjcm9zcyBwYXJ0aXRpb25zLCBwb3N0c191bmlxdWUgY291bnRzIHRoZQog"
        "ICAgICAgICMgdW5pb24uIElmIHVuaXF1ZSBpcyBzdHVjayBuZWFyIDEsMDAwIHRoZSBwYXJ0aXRp"
        "b25pbmcgaXMgbm90IHdvcmtpbmcuCiAgICAgICAgcHJpbnQoZiIgIHtoWydxdWVyaWVzJ119IHBh"
        "cnRpdGlvbnMgwrcge2hbJ3Bvc3RzX3JhdyddOix9IGhpdHMgLT4gIgogICAgICAgICAgICAgIGYi"
        "e2hbJ3Bvc3RzX3VuaXF1ZSddOix9IFVOSVFVRSBwb3N0cyAiCiAgICAgICAgICAgICAgZiIoe2hb"
        "J3Bvc3RzX3JhdyddIC0gaFsncG9zdHNfdW5pcXVlJ106LH0gZHVwbGljYXRlcyBhY3Jvc3MgIgog"
        "ICAgICAgICAgICAgIGYicGFydGl0aW9ucykgwrcge2hbJ2NvbW1lbnRzJ106LH0gY29tbWVudHMi"
        "KQogICAgd3JpdGUocmVzLCBhLm1vbnRocykKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgog"
        "ICAgbWFpbigpCg=="
    ),
}

def _install(name):
    """Register an embedded module so normal `import name` finds it."""
    mod = _types.ModuleType(name)
    mod.__file__ = f"<embedded:{name}>"
    mod.__package__ = ""
    _sys.modules[name] = mod
    exec(compile(_b64.b64decode(_EMBEDDED[name]).decode("utf-8"),
                 mod.__file__, "exec"), mod.__dict__)
    return mod

for _n in ['classify_target_consumers', 'flavor_mentions', 'reddit_collector']:
    _install(_n)

# --------------------------------------------------------------------------
# Below: capstone/run_reddit_deep.py, verbatim.
# --------------------------------------------------------------------------
#!/usr/bin/env python3
"""RUN THIS ONE. Deep Reddit pull for r/EnergyDrinks — open in VS Code and hit Run.

    python capstone/run_reddit_deep.py --self-test   # no credentials, no network
    python capstone/run_reddit_deep.py --dry-run     # show the plan, call nothing
    python capstone/run_reddit_deep.py               # real pull, bounded (see below)

WHY THIS FILE EXISTS
--------------------
capstone/collectors/reddit_collector.py is the implementation and takes a dozen
flags. This is the front door: deep mode on by default, a bounded first run so
nobody accidentally starts a 14-hour job, credentials loaded from a .env file
the way VS Code users expect, and a self-test that proves the whole chain works
before you spend any quota.

It deliberately does NOT re-implement the flavor rules. CLAUDE.md records what
happened the last time those were hand-copied into a second file: the copy got
cherry and mango wrong and silently disagreed with every other page in the
project. One definition, imported.

CREDENTIALS
-----------
Create a **script** app at https://www.reddit.com/prefs/apps, then either export
the three variables, or — easier in VS Code — copy capstone/.env.example to
capstone/.env and fill it in. .env is gitignored; it will not be committed.

BEFORE THE FIRST REAL RUN
-------------------------
Read capstone/REDDIT_API_TERMS.md. The project brief makes a current terms
summary a precondition, and deep mode issues a lot more requests than the
original plan did, which makes the free-tier request-cap question load-bearing.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Import the real implementation. Both paths are needed: `collectors` for the
# collector itself, `data/scripts` because the extractor rolls flavors up using
# the same classifier the PDI side uses.
# (bundled: modules are embedded above, no path setup needed)



def load_dotenv(path):
    """Minimal .env reader — no dependency, because asking someone to pip
    install python-dotenv before they can run one script is a bad trade.
    Ignores blanks and comments, strips optional quotes, and never overwrites a
    variable that is already set in the real environment."""
    if not os.path.exists(path):
        return 0
    n = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and not os.environ.get(k):
                os.environ[k] = v
                n += 1
    return n


def setup_env():
    """Write a .env beside this script, interactively.

    WHY INTERACTIVE RATHER THAN A TEMPLATE TO EDIT
    A pasted `export REDDIT_CLIENT_SECRET=...` lands in shell history in
    plaintext, and a filled-in template tends to get mailed, uploaded or
    committed. Reading the secret with getpass keeps it off the screen and out
    of history, and the file is written 0600 so it is readable only by you.

    The secret is never echoed, never logged, and never leaves this machine.
    """
    import getpass
    import stat

    path = os.path.join(HERE, ".env")
    if os.path.exists(path):
        print(f"\n  {path} already exists.")
        if input("  Overwrite it? [y/N] ").strip().lower() not in ("y", "yes"):
            print("  Left alone.")
            return 0

    print(f"""
  Creating {path}

  Get these from your app at https://www.reddit.com/prefs/apps
    Client ID     — shown under the app name (or in the Edit App panel)
    Client secret — the 'secret' field; typing it here will NOT be shown

  If you have ever pasted the secret into a chat, an email or a screenshot,
  regenerate it on that page FIRST and use the new one here.
""")
    cid = input("  Client ID: ").strip()
    sec = getpass.getpass("  Client secret (hidden): ").strip()
    user = input("  Your Reddit username (no /u/): ").strip().lstrip("/").removeprefix("u/")

    if not (cid and sec and user):
        print("\n  All three are required. Nothing written.")
        return 1
    if len(sec) < 10:
        print("\n  That secret looks too short — check you copied the whole "
              "'secret' field and not the Client ID. Nothing written.")
        return 1

    ua = f"script:energydrink-capstone:v1 (by /u/{user})"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# Reddit Data API credentials. Local only — never commit, "
                 "upload or paste these.\n"
                 "# Regenerate the secret at https://www.reddit.com/prefs/apps "
                 "if it is ever exposed.\n")
        fh.write(f"REDDIT_CLIENT_ID={cid}\n")
        fh.write(f"REDDIT_CLIENT_SECRET={sec}\n")
        fh.write(f"REDDIT_USER_AGENT={ua}\n")
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)        # 0600, owner only

    print(f"""
  Written, permissions 0600 (only your user can read it).
    user agent: {ua}

  Verify, then do a small first run:
    python3 {sys.argv[0]} --self-test
    python3 {sys.argv[0]} --max-posts 500
""")
    return 0


def check_auth():
    """Diagnose a credential/auth failure without guessing.

    Prints what is actually being sent - lengths and shape, never the secret
    itself - then makes one token call and reports exactly what came back.
    Written after a 403 whose traceback said only "Forbidden", which is not
    enough to act on.
    """
    import urllib.error
    import urllib.request

    env_file = os.path.join(HERE, ".env")
    print(f"\n  CHECK-AUTH\n\n  .env: {env_file}"
          f"  {'(found)' if os.path.exists(env_file) else '(MISSING)'}")
    if os.path.exists(env_file):
        mode = oct(os.stat(env_file).st_mode & 0o777)
        print(f"  permissions: {mode}" +
              ("" if mode == "0o600" else "   <- consider chmod 600"))

    cid = os.environ.get("REDDIT_CLIENT_ID", "")
    sec = os.environ.get("REDDIT_CLIENT_SECRET", "")
    agent = os.environ.get("REDDIT_USER_AGENT", "")

    def shape(v):
        v = v.strip()
        if not v:
            return "EMPTY"
        lead = v[:3] + "..." + v[-2:] if len(v) > 8 else "(short)"
        note = ""
        if v != os.environ.get("", v) and (v.startswith(('"', "'")) or v.endswith(('"', "'"))):
            note = "   <- has surrounding quotes, remove them"
        return f"{len(v)} chars  {lead}{note}"

    print(f"\n  REDDIT_CLIENT_ID      {shape(cid)}")
    print(f"  REDDIT_CLIENT_SECRET  {shape(sec)}")
    print(f"  REDDIT_USER_AGENT     {agent!r}")

    problems = []
    if not cid.strip():
        problems.append("client id is empty")
    if not sec.strip():
        problems.append("client secret is empty")
    if not agent.strip():
        problems.append("user agent is empty")
    # The single most common 403 cause.
    if "<" in agent or ">" in agent:
        problems.append("USER AGENT STILL HAS A PLACEHOLDER — the literal "
                        "'<you>' must be replaced with your Reddit username")
    if agent.strip() and "by /u/" not in agent:
        problems.append("user agent has no 'by /u/<username>' — Reddit wants "
                        "a contactable identifier and throttles generic agents")
    if len(sec.strip()) < 20:
        problems.append(f"secret is only {len(sec.strip())} chars — Reddit "
                        "secrets are longer; did the Client ID get pasted here?")
    if cid.strip() and sec.strip() and cid.strip() == sec.strip():
        problems.append("client id and secret are identical")

    if problems:
        print("\n  PROBLEMS FOUND:")
        for p_ in problems:
            print(f"    - {p_}")
        print("\n  Fix those first; a token call will fail until they are fixed.")
        return 1

    print("\n  Shape looks right. Trying one token call ...")
    import base64
    import urllib.parse
    data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    auth = base64.b64encode(f"{cid.strip()}:{sec.strip()}".encode()).decode()
    req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token", data=data,
        headers={"Authorization": "Basic " + auth, "User-Agent": agent.strip()})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.load(r)
        if "access_token" in body:
            print(f"\n  SUCCESS — token received "
                  f"(type {body.get('token_type')}, expires in "
                  f"{body.get('expires_in')}s, scope {body.get('scope')!r})")
            print("  Credentials work. Run the real pull:\n"
                  f"    python3 {sys.argv[0]} --max-posts 500\n")
            return 0
        print(f"\n  Unexpected response with no token: {body}")
        return 1
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "replace")[:800].strip()
        except Exception:
            pass
        print(f"\n  HTTP {e.code} {e.reason}")
        print(f"  Reddit said: {body or '(empty body)'}")
        print(f"""
  For a {e.code}, check in this order:
    403  - the User-Agent above. Reddit blocks generic and malformed ones.
         - the separate "register to use the API" step linked from
           https://www.reddit.com/prefs/apps — creating the app is not enough.
         - the Responsible Builder Policy acceptance.
         - a VPN or shared IP that Reddit has blocked.
    401  - wrong id/secret, or the app is not type 'script'. If you regenerated
           the secret, .env must have the NEW one.
    429  - rate limited; wait a few minutes.
""")
        return 1
    except urllib.error.URLError as e:
        print(f"\n  Could not reach Reddit at all: {e.reason}")
        print("  Network, DNS or firewall — not a credentials problem.")
        return 1


def preflight():
    """Fail with something actionable rather than a traceback."""
    missing = [k for k in ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET",
                           "REDDIT_USER_AGENT") if not os.environ.get(k)]
    if not missing:
        return True
    me = sys.argv[0] or os.path.abspath(__file__)
    print("\n  Missing credentials:", ", ".join(missing))
    env_path = os.path.join(HERE, ".env")
    tmpl = os.path.join(HERE, ".env.example")
    # The bundled copy has no .env.example beside it, so offer to write one
    # rather than pointing at a file that is not there.
    step1 = (f"1. Fill in the template:\n       {tmpl}\n       -> save as {env_path}"
             if os.path.exists(tmpl) else
             f"1. Run this and follow the prompts (easiest):\n"
             f"       python3 {sys.argv[0]} --setup\n\n"
             f"   Or create {env_path} by hand with these three lines:\n"
             f"       REDDIT_CLIENT_ID=...\n"
             f"       REDDIT_CLIENT_SECRET=...\n"
             f'       REDDIT_USER_AGENT=script:bogus-banana-capstone:v1 (by /u/<you>)')
    print(f"""
  Two ways to fix it:

  {step1}

  2. Or export them in your shell:
       export REDDIT_CLIENT_ID=...
       export REDDIT_CLIENT_SECRET=...
       export REDDIT_USER_AGENT="script:bogus-banana-capstone:v1 (by /u/<you>)"

  Get the values by creating a **script** app at
  https://www.reddit.com/prefs/apps  (the client id is the string under the app
  name; the secret is the field labelled "secret").

  No credentials needed to try these first:
       python3 {me} --self-test
       python3 {me} --dry-run
""")
    return False


def self_test():
    """Prove the whole chain works before spending any quota or credentials.

    Runs three things:
      1. the extractor against real committed text (so you see actual output),
      2. the partitioning logic against a mock Reddit that enforces the real
         1,000-item listing cap,
      3. the CSV writer, into a temp dir.

    No network. No credentials. If this passes, the only thing standing between
    you and a real pull is the three environment variables.
    """
    import tempfile
    import csv as _csv
    ok, fail = [], []

    # -- 1. extractor on real text ------------------------------------------
    try:
        from flavor_mentions import extract, analyse
        f, b, _ = extract("The bang mocha was the greatest flavor out! "
                          "Way better than the watermelon one.")
        assert "Coffee" in f, f"expected Coffee in {f}"
        assert "Watermelon" in f, f"expected Watermelon in {f}"
        assert "Bang" in b, f"expected Bang in {b}"
        ok.append(f"extractor: flavors={sorted(f)} brands={sorted(b)}")

        # the context gate must still reject a bare competing-beverage mention
        f2, _, _ = extract("I only have 1 cup of coffee in the morning")
        assert "Coffee" not in f2, f"context gate leaked: {f2}"
        ok.append("context gate: 'cup of coffee in the morning' correctly NOT a flavor")

        corpus = os.path.join(ROOT, "data/youtube/comments.csv")
        if os.path.exists(corpus):
            _csv.field_size_limit(10 ** 7)
            with open(corpus, encoding="utf-8", errors="replace") as fh:
                res = analyse(_csv.DictReader(fh), limit=5000)
            top = ", ".join(f"{r['name']}({r['mentions']})" for r in res["flavors"][:5])
            ok.append(f"real corpus: {res['rows_matched']:,}/{res['rows_seen']:,} matched "
                      f"({res['match_rate_pct']}%) · top: {top}")
        else:
            ok.append("real corpus: skipped (data/youtube/comments.csv not present)")
    except Exception as e:
        fail.append(f"extractor: {type(e).__name__}: {e}")

    # -- 2. partitioning beats the 1,000 cap --------------------------------
    try:
        import reddit_collector as rc
        cap = rc.LISTING_CAP
        TOTAL = 25_000

        def fake_get(path, tok, quota, **p):
            quota.calls += 1
            if "/comments/" in path:
                pid = path.rsplit("/", 1)[-1]
                return [{}, {"data": {"children": [
                    {"kind": "t1", "data": {"body": f"c{i} {pid} mango flavor"}}
                    for i in range(5)]}}]
            seed = hash((p.get("q"), p.get("sort"), p.get("t"))) % TOTAL
            off = int(p.get("after") or 0)
            if off >= cap:
                return {"data": {"children": [], "after": None}}
            kids = [{"data": {"id": f"p{(seed+off+i) % TOTAL}",
                              "created_utc": 1_700_000_000 + i,
                              "title": "watermelon flavor post", "selftext": ""}}
                    for i in range(rc.PAGE)]
            nxt = off + rc.PAGE
            return {"data": {"children": kids,
                             "after": str(nxt) if nxt < cap else None}}

        real_get, real_sleep, real_subs = rc.get, rc.SLEEP, rc.SUBREDDITS
        rc.get, rc.SLEEP, rc.SUBREDDITS = fake_get, 0, ["EnergyDrinks"]
        q = rc.Quota()
        rc.SEARCH_TERMS = ["flavor"]
        list(rc.harvest("mock", q, months=600, verbose=False, deep=False))
        std = rc.harvest.stats["posts_unique"]
        rc.DEEP_TERMS = ["the", "it", "a", "flavor", "best", "worst"]
        rc.DEEP_SORTS, rc.DEEP_WINDOWS = ["new", "top", "relevance"], ["all", "year"]
        texts = list(rc.harvest("mock", q, months=600, verbose=False, deep=True))
        deep = rc.harvest.stats
        rc.get, rc.SLEEP, rc.SUBREDDITS = real_get, real_sleep, real_subs

        assert std <= cap, f"standard mode returned {std}, above the cap — mock is wrong"
        assert deep["posts_unique"] > cap, (
            f"deep mode got {deep['posts_unique']:,}, did NOT beat the {cap:,} cap")
        ok.append(f"standard mode: {std:,} unique posts (capped at {cap:,}, as expected)")
        ok.append(f"deep mode:     {deep['posts_unique']:,} unique posts "
                  f"— {deep['posts_unique']/cap:.0f}x past the cap")
        ok.append(f"dedupe:        {deep['posts_raw']:,} raw hits -> "
                  f"{deep['posts_raw']-deep['posts_unique']:,} duplicates removed")
        ok.append(f"comment walk:  {deep['comments']:,} comments, {len(texts):,} texts total")
    except Exception as e:
        fail.append(f"partitioning: {type(e).__name__}: {e}")

    # -- 3. credentials are read at CALL time, not import time --------------
    # Regression guard. reddit_collector had `UA = os.environ.get(...)` at
    # module level; the bundle installs modules before main() loads the .env,
    # so UA was frozen as "" and a real run died with "Missing credentials"
    # immediately after reporting it had loaded three variables. Any env read
    # that happens at import time reintroduces this, so the test sets the
    # variables AFTER the import and asserts the collector still sees them.
    try:
        import reddit_collector as rc2
        saved = {k: os.environ.get(k) for k in
                 ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT")}
        try:
            os.environ["REDDIT_CLIENT_ID"] = "probe_id"
            os.environ["REDDIT_CLIENT_SECRET"] = "probe_secret_value"
            os.environ["REDDIT_USER_AGENT"] = "script:probe:v1 (by /u/probe)"
            assert rc2.ua() == "script:probe:v1 (by /u/probe)", (
                f"user agent read at import time, not call time: {rc2.ua()!r}")
            # token() must get past its own credential check and fail only on
            # the network call, which is what SystemExit here would rule out.
            try:
                rc2.token()
            except SystemExit as e:
                raise AssertionError(
                    f"credential check rejected env vars set after import: {e}")
            except Exception:
                pass          # network failure is expected and fine
            ok.append("credentials: read at call time, survive a late .env load")
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    except AssertionError as e:
        fail.append(f"credentials: {e}")
    except Exception as e:
        fail.append(f"credentials: {type(e).__name__}: {e}")

    # -- 4. writer ----------------------------------------------------------
    try:
        import reddit_collector as rc
        with tempfile.TemporaryDirectory() as tmp:
            real_out = rc.OUT_DIR
            rc.OUT_DIR = tmp
            rc.write({"flavors": [{"name": "Mango", "mentions": 3}],
                      "brands": [{"name": "Bang", "mentions": 2}],
                      "rows_seen": 3, "rows_matched": 3, "match_rate_pct": 100.0,
                      "engine": "test", "quota": {"calls": 1}}, months=24)
            rc.OUT_DIR = real_out
            assert len(os.listdir(tmp)) == 3, os.listdir(tmp)
        ok.append("writer: 3 CSVs written and verified")
    except Exception as e:
        fail.append(f"writer: {type(e).__name__}: {e}")

    print("\n  SELF-TEST — no network, no credentials\n")
    for line in ok:
        print(f"    ok   {line}")
    for line in fail:
        print(f"    FAIL {line}")
    if fail:
        print(f"\n  {len(fail)} FAILED\n")
        return 1
    creds = all(os.environ.get(k) for k in
                ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT"))
    print(f"\n  ALL PASSED — the pipeline works end to end.")
    print(f"  Credentials: {'found, you can do a real run' if creds else 'NOT set — see --help'}\n")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="Deep Reddit pull for the flavor study.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)
    ap.add_argument("--check-auth", action="store_true",
                    help="diagnose credential/auth failures; makes ONE token call "
                         "and reports exactly what Reddit said")
    ap.add_argument("--setup", action="store_true",
                    help="create the .env credentials file interactively "
                         "(secret is typed hidden, never echoed or logged)")
    ap.add_argument("--self-test", action="store_true",
                    help="verify the whole chain offline, then exit")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan without making a single call")
    ap.add_argument("--max-posts", type=int, default=2000,
                    help="stop after N UNIQUE posts. Default 2000 (~35-45 min) so a "
                         "first run is bounded; raise it once you have seen the output. "
                         "0 means no limit and is a multi-hour job.")
    ap.add_argument("--months", type=int, default=36,
                    help="how far back to keep posts (default 36)")
    ap.add_argument("--standard", action="store_true",
                    help="use the narrow non-partitioned plan instead of deep mode")
    a = ap.parse_args()

    env_file = os.path.join(HERE, ".env")
    n = load_dotenv(env_file)
    if n:
        # The real path, not a hardcoded repo-relative one. The bundled copy
        # lives wherever the user put it, and printing "capstone/.env" to
        # someone whose file is on their Desktop is just confusing.
        print(f"  loaded {n} variable(s) from {env_file}")

    if a.setup:
        sys.exit(setup_env())
    if a.check_auth:
        sys.exit(check_auth())
    if a.self_test:
        sys.exit(self_test())

    import reddit_collector as rc
    deep = not a.standard

    if a.dry_run:
        rc.plan(deep)
        return
    if not preflight():
        sys.exit(1)

    print(f"\n  Deep pull starting. Ctrl-C is safe — responses are cached, so a "
          f"restart resumes.\n  Bound: {a.max_posts or 'NONE (multi-hour)'} unique posts, "
          f"{a.months} months back.\n")
    res = rc.run(a.months, limit=None, verbose=True, deep=deep,
                 max_posts=a.max_posts or None)
    h = res.get("harvest", {})
    print(f"\n  {res['rows_seen']:,} texts · {res['rows_matched']:,} matched "
          f"({res['match_rate_pct']}%) · {res['quota']['calls']} API calls")
    if h:
        print(f"  {h['queries']} partitions · {h['posts_raw']:,} hits -> "
              f"{h['posts_unique']:,} UNIQUE posts "
              f"({h['posts_raw']-h['posts_unique']:,} dupes) · {h['comments']:,} comments")
        if h["posts_unique"] > rc.LISTING_CAP:
            print(f"  -> cleared the {rc.LISTING_CAP:,}-item listing cap")
    rc.write(res, a.months)
    print("\n  Top flavors:")
    for r in res["flavors"][:10]:
        print(f"    {r['name']:<16}{r['mentions']:>7,}  {r['mention_share_pct']:>6}% "
              f" net {r['net_sentiment']:>6}")
    print()


if __name__ == "__main__":
    main()
