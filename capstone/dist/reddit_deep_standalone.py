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
#  Built 2026-09-21 21:33 UTC from 28f7d27
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
        "dCIpCkNBQ0hFX0RJUiA9IG9zLnBhdGguam9pbihST09ULCAiLmNhY2hlL3JlZGRpdCIpClVBID0g"
        "b3MuZW52aXJvbi5nZXQoIlJFRERJVF9VU0VSX0FHRU5UIiwgIiIpCgojIFN1YnJlZGRpdCBuYW1l"
        "cyBhcmUgY2FzZS1pbnNlbnNpdGl2ZSBvbiBSZWRkaXQsIHNvICJlbmVyZ3lkcmlua3MiIGFuZAoj"
        "ICJFbmVyZ3lEcmlua3MiIGFyZSBvbmUgc3VicmVkZGl0IGFuZCBsaXN0aW5nIGJvdGggYnVybmVk"
        "IGhhbGYgdGhlIGNhbGxzIG9uCiMgdGhvc2Ugcm93cyB0d2ljZS4gRGVkdXBlZCBjYXNlLWluc2Vu"
        "c2l0aXZlbHkgYmVsb3cgcmF0aGVyIHRoYW4gYnkgaGFuZCwgc28gYQojIGZ1dHVyZSBlZGl0IGNh"
        "bm5vdCByZWludHJvZHVjZSBpdC4KX1NVQlMgPSBbIkVuZXJneURyaW5rcyIsICJjYWZmZWluZSIs"
        "ICJDZWxzaXVzX09mZmljaWFsIiwgIk1vbnN0ZXJFbmVyZ3kiLAogICAgICAgICAiYmFuZ19lbmVy"
        "Z3kiLCAiQWxhbmlOdSIsICJHaG9zdEVuZXJneSJdClNVQlJFRERJVFMgPSBsaXN0KHtzLmxvd2Vy"
        "KCk6IHMgZm9yIHMgaW4gX1NVQlN9LnZhbHVlcygpKQoKIyBQcmUtcmVnaXN0ZXJlZCBzZWFyY2gg"
        "dGVybXMuIFByb3Bvc2VkLCBub3Qgc2V0dGxlZCAtIHRoZSBicmllZiBzYXlzIENhaQojIGFwcHJv"
        "dmVzIHRoZXNlIGJlZm9yZSBhIHJlYWwgcnVuLCBzbyB0aGV5IGxpdmUgaGVyZSB0byBiZSByZXZp"
        "ZXdlZC4KU0VBUkNIX1RFUk1TID0gWyJlbmVyZ3kgZHJpbmsgZmxhdm9yIiwgImVuZXJneSBkcmlu"
        "ayB0YXN0ZSIsICJiZXN0IGZsYXZvciIsCiAgICAgICAgICAgICAgICAid29yc3QgZmxhdm9yIiwg"
        "Im5ldyBmbGF2b3IiLCAiZmxhdm9yIHJldmlldyIsICJ0aWVyIGxpc3QiXQoKIyBSZWRkaXQncyBk"
        "b2N1bWVudGVkIGZyZWUgdGllciBmb3IgYW4gT0F1dGggc2NyaXB0IGFwcCBpcyAxMDAgcXVlcmll"
        "cyBwZXIKIyBtaW51dGUgYXZlcmFnZWQgb3ZlciBhIDEwLW1pbnV0ZSB3aW5kb3cuIFRoaXMgcGFj"
        "ZXMgd2VsbCB1bmRlciB0aGF0OiB0aGUKIyBjb2xsZWN0b3IgaXMgbm90IHRoZSBib3R0bGVuZWNr"
        "IGluIGFueW9uZSdzIGRheSBhbmQgYmVpbmcgYSBnb29kIGNsaWVudCBpcwojIGNoZWFwZXIgdGhh"
        "biBiZWluZyByYXRlLWxpbWl0ZWQuIFZFUklGWSBUSElTIE5VTUJFUiBhZ2FpbnN0IGN1cnJlbnQg"
        "ZG9jcyAtCiMgaXQgaXMgZXhhY3RseSB0aGUgc29ydCBvZiBmaWd1cmUgdGhhdCBjaGFuZ2VzIChz"
        "ZWUgUkVERElUX0FQSV9URVJNUy5tZCkuClFQTV9CVURHRVQgPSA2MApTTEVFUCA9IDYwLjAgLyBR"
        "UE1fQlVER0VUCgpUT0tFTl9VUkwgPSAiaHR0cHM6Ly93d3cucmVkZGl0LmNvbS9hcGkvdjEvYWNj"
        "ZXNzX3Rva2VuIgpBUEkgPSAiaHR0cHM6Ly9vYXV0aC5yZWRkaXQuY29tIgoKCmNsYXNzIFF1b3Rh"
        "OgogICAgIiIiQ291bnRzIGNhbGxzIGFuZCByZWFkcyBSZWRkaXQncyBvd24gcmF0ZS1saW1pdCBo"
        "ZWFkZXJzIGJhY2ssIHNvIHRoZQogICAgY29sbGVjdG9yIHJlcG9ydHMgd2hhdCB0aGUgc2VydmVy"
        "IHNhaWQgcmF0aGVyIHRoYW4gd2hhdCBpdCBhc3N1bWVkLiIiIgoKICAgIGRlZiBfX2luaXRfXyhz"
        "ZWxmKToKICAgICAgICBzZWxmLmNhbGxzID0gMAogICAgICAgIHNlbGYucmVtYWluaW5nID0gTm9u"
        "ZQogICAgICAgIHNlbGYucmVzZXQgPSBOb25lCiAgICAgICAgc2VsZi5zdGFydGVkID0gdGltZS50"
        "aW1lKCkKCiAgICBkZWYgbm90ZShzZWxmLCBoZWFkZXJzKToKICAgICAgICBzZWxmLmNhbGxzICs9"
        "IDEKICAgICAgICBmb3IgaywgYXR0ciBpbiAoKCJ4LXJhdGVsaW1pdC1yZW1haW5pbmciLCAicmVt"
        "YWluaW5nIiksCiAgICAgICAgICAgICAgICAgICAgICAgICgieC1yYXRlbGltaXQtcmVzZXQiLCAi"
        "cmVzZXQiKSk6CiAgICAgICAgICAgIHYgPSBoZWFkZXJzLmdldChrKQogICAgICAgICAgICBpZiB2"
        "IGlzIG5vdCBOb25lOgogICAgICAgICAgICAgICAgdHJ5OgogICAgICAgICAgICAgICAgICAgIHNl"
        "dGF0dHIoc2VsZiwgYXR0ciwgZmxvYXQodikpCiAgICAgICAgICAgICAgICBleGNlcHQgVmFsdWVF"
        "cnJvcjoKICAgICAgICAgICAgICAgICAgICBwYXNzCgogICAgZGVmIHJlcG9ydChzZWxmKToKICAg"
        "ICAgICBtaW5zID0gKHRpbWUudGltZSgpIC0gc2VsZi5zdGFydGVkKSAvIDYwIG9yIDFlLTkKICAg"
        "ICAgICByZXR1cm4geyJjYWxscyI6IHNlbGYuY2FsbHMsICJjYWxsc19wZXJfbWluIjogcm91bmQo"
        "c2VsZi5jYWxscyAvIG1pbnMsIDEpLAogICAgICAgICAgICAgICAgInNlcnZlcl9yZW1haW5pbmci"
        "OiBzZWxmLnJlbWFpbmluZywgInNlcnZlcl9yZXNldF9zIjogc2VsZi5yZXNldH0KCgojIC0tLS0t"
        "LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "IGNvbGxlY3RvciAtLQpkZWYgdG9rZW4oKToKICAgICIiIk9BdXRoMiBjbGllbnQtY3JlZGVudGlh"
        "bHMgZ3JhbnQuIFJhaXNlcyByYXRoZXIgdGhhbiBkZWdyYWRpbmc6IHRoZXJlIGlzCiAgICBkZWxp"
        "YmVyYXRlbHkgbm8gdW5hdXRoZW50aWNhdGVkIHBhdGggdG8gZmFsbCBiYWNrIHRvLiIiIgogICAg"
        "Y2lkID0gb3MuZW52aXJvbi5nZXQoIlJFRERJVF9DTElFTlRfSUQiLCAiIikuc3RyaXAoKQogICAg"
        "c2VjID0gb3MuZW52aXJvbi5nZXQoIlJFRERJVF9DTElFTlRfU0VDUkVUIiwgIiIpLnN0cmlwKCkK"
        "ICAgIGlmIG5vdCAoY2lkIGFuZCBzZWMgYW5kIFVBKToKICAgICAgICBzeXMuZXhpdCgKICAgICAg"
        "ICAgICAgIk1pc3NpbmcgY3JlZGVudGlhbHMuIFNldCBhbGwgdGhyZWUsIHRoZW4gcmVydW46XG4i"
        "CiAgICAgICAgICAgICIgIGV4cG9ydCBSRURESVRfQ0xJRU5UX0lEPS4uLlxuIgogICAgICAgICAg"
        "ICAiICBleHBvcnQgUkVERElUX0NMSUVOVF9TRUNSRVQ9Li4uXG4iCiAgICAgICAgICAgICcgIGV4"
        "cG9ydCBSRURESVRfVVNFUl9BR0VOVD0ic2NyaXB0OmJvZ3VzLWJhbmFuYS1jYXBzdG9uZTp2MSAo"
        "YnkgL3UvPHlvdT4pIlxuJwogICAgICAgICAgICAiQ3JlYXRlIGEgKnNjcmlwdCogYXBwIGF0IGh0"
        "dHBzOi8vd3d3LnJlZGRpdC5jb20vcHJlZnMvYXBwcyIpCiAgICBkYXRhID0gdXJsbGliLnBhcnNl"
        "LnVybGVuY29kZSh7ImdyYW50X3R5cGUiOiAiY2xpZW50X2NyZWRlbnRpYWxzIn0pLmVuY29kZSgp"
        "CiAgICBpbXBvcnQgYmFzZTY0CiAgICBhdXRoID0gYmFzZTY0LmI2NGVuY29kZShmIntjaWR9Ontz"
        "ZWN9Ii5lbmNvZGUoKSkuZGVjb2RlKCkKICAgIHJlcSA9IHVybGxpYi5yZXF1ZXN0LlJlcXVlc3Qo"
        "VE9LRU5fVVJMLCBkYXRhPWRhdGEsIGhlYWRlcnM9ewogICAgICAgICJBdXRob3JpemF0aW9uIjog"
        "IkJhc2ljICIgKyBhdXRoLCAiVXNlci1BZ2VudCI6IFVBfSkKICAgIHdpdGggdXJsbGliLnJlcXVl"
        "c3QudXJsb3BlbihyZXEsIHRpbWVvdXQ9MzApIGFzIHI6CiAgICAgICAgcmV0dXJuIGpzb24ubG9h"
        "ZChyKVsiYWNjZXNzX3Rva2VuIl0KCgpkZWYgZ2V0KHBhdGgsIHRvaywgcXVvdGEsICoqcGFyYW1z"
        "KToKICAgICIiIk9uZSBhdXRoZW50aWNhdGVkIEdFVC4gQ2FjaGVzIGJ5IFVSTCBzbyBhIHJlLXJ1"
        "biBjb3N0cyBub3RoaW5nIGFuZCBhbgogICAgaW50ZXJydXB0ZWQgcnVuIHJlc3VtZXMgLSB3aGlj"
        "aCBtYXR0ZXJzIHdoZW4gYSBmdWxsIHB1bGwgaXMgdGhvdXNhbmRzIG9mCiAgICBjYWxscyBhbmQg"
        "UmVkZGl0J3MgbGlzdGluZ3Mgc2hpZnQgdW5kZXIgeW91LiIiIgogICAgdXJsID0gZiJ7QVBJfXtw"
        "YXRofT97dXJsbGliLnBhcnNlLnVybGVuY29kZShwYXJhbXMpfSIKICAgIGtleSA9IG9zLnBhdGgu"
        "am9pbihDQUNIRV9ESVIsIHN0cihhYnMoaGFzaCh1cmwpKSkgKyAiLmpzb24iKQogICAgaWYgb3Mu"
        "cGF0aC5leGlzdHMoa2V5KToKICAgICAgICB3aXRoIG9wZW4oa2V5KSBhcyBmaDoKICAgICAgICAg"
        "ICAgcmV0dXJuIGpzb24ubG9hZChmaCkKICAgIHJlcSA9IHVybGxpYi5yZXF1ZXN0LlJlcXVlc3Qo"
        "dXJsLCBoZWFkZXJzPXsKICAgICAgICAiQXV0aG9yaXphdGlvbiI6ICJCZWFyZXIgIiArIHRvaywg"
        "IlVzZXItQWdlbnQiOiBVQX0pCiAgICBmb3IgYXR0ZW1wdCBpbiByYW5nZSg0KToKICAgICAgICB0"
        "cnk6CiAgICAgICAgICAgIHdpdGggdXJsbGliLnJlcXVlc3QudXJsb3BlbihyZXEsIHRpbWVvdXQ9"
        "NDUpIGFzIHI6CiAgICAgICAgICAgICAgICBxdW90YS5ub3RlKHtrLmxvd2VyKCk6IHYgZm9yIGss"
        "IHYgaW4gci5oZWFkZXJzLml0ZW1zKCl9KQogICAgICAgICAgICAgICAgYm9keSA9IGpzb24ubG9h"
        "ZChyKQogICAgICAgICAgICBvcy5tYWtlZGlycyhDQUNIRV9ESVIsIGV4aXN0X29rPVRydWUpCiAg"
        "ICAgICAgICAgIHdpdGggb3BlbihrZXksICJ3IikgYXMgZmg6CiAgICAgICAgICAgICAgICBqc29u"
        "LmR1bXAoYm9keSwgZmgpCiAgICAgICAgICAgIHRpbWUuc2xlZXAoU0xFRVApCiAgICAgICAgICAg"
        "IHJldHVybiBib2R5CiAgICAgICAgZXhjZXB0IHVybGxpYi5lcnJvci5IVFRQRXJyb3IgYXMgZToK"
        "ICAgICAgICAgICAgaWYgZS5jb2RlID09IDQyOTogICAgICAgICAgICAgICMgcmF0ZSBsaW1pdGVk"
        "OiBiYWNrIG9mZiBhbmQgcmV0cnkKICAgICAgICAgICAgICAgIHRpbWUuc2xlZXAoMiAqKiBhdHRl"
        "bXB0ICogNSkKICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgIGlmIGUuY29kZSBp"
        "biAoNDAxLCA0MDMpOgogICAgICAgICAgICAgICAgc3lzLmV4aXQoZiJSZWRkaXQgcmVmdXNlZCB0"
        "aGUgcmVxdWVzdCAoe2UuY29kZX0pLiBDaGVjayB0aGUgIgogICAgICAgICAgICAgICAgICAgICAg"
        "ICAgImNyZWRlbnRpYWxzIGFuZCB0aGF0IHRoZSBhcHAgdHlwZSBpcyAnc2NyaXB0Jy4iKQogICAg"
        "ICAgICAgICByYWlzZQogICAgICAgIGV4Y2VwdCB1cmxsaWIuZXJyb3IuVVJMRXJyb3IgYXMgZToK"
        "ICAgICAgICAgICAgaWYgYXR0ZW1wdCA9PSAzOgogICAgICAgICAgICAgICAgcmFpc2UKICAgICAg"
        "ICAgICAgdGltZS5zbGVlcCgyICoqIGF0dGVtcHQgKiAyKQogICAgcmV0dXJuIE5vbmUKCgojIC0t"
        "LSBnZXR0aW5nIHBhc3QgdGhlIDEsMDAwLWl0ZW0gbGlzdGluZyBjYXAgLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tLS0tLS0tLS0KIwojIFJlZGRpdCBjYXBzIEFOWSBzaW5nbGUgbGlzdGluZyBhdCBy"
        "b3VnaGx5IDEsMDAwIGl0ZW1zLiBQYWdpbmF0aW5nIHdpdGgKIyBgYWZ0ZXJgIHBhc3QgdGhhdCBy"
        "ZXR1cm5zIG5vdGhpbmcgLSBpdCBpcyBhIHByb2R1Y3QgbGltaXQsIG5vdCBhIHJhdGUgbGltaXQs"
        "CiMgYW5kIG5vIGFtb3VudCBvZiBwYXRpZW5jZSBvciBwb2xpdGVuZXNzIGdldHMgYSAxLDAwMXN0"
        "IGl0ZW0gb3V0IG9mIG9uZSBxdWVyeS4KIwojIFlvdSBnZXQgcGFzdCBpdCBieSBQQVJUSVRJT05J"
        "TkcgdGhlIHNwYWNlIGludG8gbWFueSBzZXBhcmF0ZSBsaXN0aW5ncywgZWFjaAojIHdpdGggaXRz"
        "IG93biAxLDAwMCBjYXAsIGFuZCB0YWtpbmcgdGhlIHVuaW9uLiBUaGF0IGlzIG9yZGluYXJ5IGRv"
        "Y3VtZW50ZWQgQVBJCiMgdXNlLCBub3QgZXZhc2lvbjogZXZlcnkgY2FsbCBpcyBhbiBhdXRoZW50"
        "aWNhdGVkLCByYXRlLWxpbWl0ZWQgcmVxdWVzdCB0byBhCiMgcHVibGljIGVuZHBvaW50LiBXaGF0"
        "IGl0IGlzIE5PVCBpcyBhIGNlbnN1cyAtIHNlZSB0aGUgaG9uZXN0eSBub3RlIGJlbG93LgojCiMg"
        "VGhyZWUgYXhlcywgbXVsdGlwbHlpbmcgdG9nZXRoZXI6CiMKIyAgIDEuIFFVRVJZIFRFUk0uIEVh"
        "Y2ggZGlzdGluY3QgYHFgIGlzIGl0cyBvd24gbGlzdGluZyB3aXRoIGl0cyBvd24gY2FwLiBUaGlz"
        "CiMgICAgICBpcyB0aGUgYmlnZ2VzdCBsZXZlciwgYW5kIGl0IGlzIHdoeSB0aGUgdGVybSBsaXN0"
        "IGJlbG93IGluY2x1ZGVzIGJsYW5kCiMgICAgICBoaWdoLWZyZXF1ZW5jeSB3b3JkcyBhcyB3ZWxs"
        "IGFzIHRvcGljYWwgb25lczogInRoZSIgYW5kICJpdCIgcGFydGl0aW9uCiMgICAgICB0aGUgc3Vi"
        "cmVkZGl0IGZhciBtb3JlIGV2ZW5seSB0aGFuICJ0aWVyIGxpc3QiIGRvZXMuCiMgICAyLiBTT1JU"
        "LiBuZXcgLyB0b3AgLyByZWxldmFuY2UgLyBjb21tZW50cyBzdXJmYWNlIGRpZmZlcmVudCBzbGlj"
        "ZXMgb2YgdGhlCiMgICAgICBzYW1lIHJlc3VsdCBzZXQsIHNvIHRoZXkgb3ZlcmxhcCBoZWF2aWx5"
        "IGJ1dCBub3QgY29tcGxldGVseS4KIyAgIDMuIFRJTUUgV0lORE9XLiBgdGAgdGFrZXMgYWxsL3ll"
        "YXIvbW9udGgvd2Vlay9kYXkuIEVhY2ggaXMgYSBzZXBhcmF0ZSBjYXAsCiMgICAgICBhbmQgdGhl"
        "IG5hcnJvdyBvbmVzIHJlYWNoIGNvbnRlbnQgdGhlIGBhbGxgIGxpc3RpbmcgaGFzIGxvbmcgYnVy"
        "aWVkLgojCiMgVGhlbiB0aGUgcmVhbCBtdWx0aXBsaWVyOiBDT01NRU5UIFRSRUVTLiBUaGUgY2Fw"
        "IGFwcGxpZXMgdG8gcG9zdCBsaXN0aW5ncy4KIyBFYWNoIHVuaXF1ZSBwb3N0J3MgY29tbWVudHMg"
        "YXJlIGEgc2VwYXJhdGUgZmV0Y2gsIGFuZCB0YXN0ZSB0YWxrIGxpdmVzIGluIHRoZQojIGNvbW1l"
        "bnRzIGFueXdheS4gQSBmZXcgdGhvdXNhbmQgcG9zdHMgYXQgMTAtNDAgY29tbWVudHMgZWFjaCBp"
        "cyB3aGVyZSB0aGUKIyBjb3JwdXMgYWN0dWFsbHkgY29tZXMgZnJvbS4KIwojIEhPTkVTVFkgTk9U"
        "RSwgd2hpY2ggYmVsb25ncyBpbiB0aGUgbWV0aG9kcyBzZWN0aW9uIHRvbzogdGhlIHVuaW9uIG9m"
        "IG1hbnkKIyBjYXBwZWQgbGlzdGluZ3MgaXMgc3RpbGwgbm90IHRoZSBzdWJyZWRkaXQuIFJlZGRp"
        "dCdzIHNlYXJjaCBpbmRleCBkb2VzIG5vdAojIHJlbGlhYmx5IHN1cmZhY2UgdmVyeSBvbGQgb3Ig"
        "bG93LWVuZ2FnZW1lbnQgcG9zdHMgYXQgYWxsLCBzbyBjb3ZlcmFnZSBkZWNheXMKIyB3aXRoIGFn"
        "ZSBpbiBhIHdheSB0aGlzIGNhbm5vdCBtZWFzdXJlIGZyb20gdGhlIGluc2lkZS4gUmVwb3J0IHdo"
        "YXQgd2FzCiMgY29sbGVjdGVkLCBuZXZlciBpbXBseSBjb21wbGV0ZW5lc3MuCgpERUVQX1RFUk1T"
        "ID0gWwogICAgIyBoaWdoLWZyZXF1ZW5jeSBwYXJ0aXRpb25lcnMgLSB0aGVzZSBkbyB0aGUgaGVh"
        "dnkgbGlmdGluZwogICAgInRoZSIsICJpdCIsICJhIiwgImFuZCIsICJpcyIsICJteSIsICJ0aGlz"
        "IiwgInlvdSIsICJidXQiLCAibm90IiwKICAgICMgdG9waWNhbCwgZm9yIHByZWNpc2lvbiBvbiB0"
        "aGUgZmxhdm9yIHF1ZXN0aW9uCiAgICAiZmxhdm9yIiwgImZsYXZvdXIiLCAidGFzdGUiLCAidGFz"
        "dGVzIiwgImJlc3QiLCAid29yc3QiLCAibmV3IiwgInRyaWVkIiwKICAgICJyZXZpZXciLCAidGll"
        "ciBsaXN0IiwgImZhdm9yaXRlIiwgInN1Z2FyIiwgImNhZmZlaW5lIiwgImNhbiIsICJkcmluayIs"
        "Cl0KREVFUF9TT1JUUyA9IFsibmV3IiwgInRvcCIsICJyZWxldmFuY2UiLCAiY29tbWVudHMiXQpE"
        "RUVQX1dJTkRPV1MgPSBbImFsbCIsICJ5ZWFyIiwgIm1vbnRoIl0KClBBR0UgPSAxMDAgICAgICAg"
        "ICAgIyBtYXggUmVkZGl0IHJldHVybnMgcGVyIGNhbGwKTElTVElOR19DQVAgPSAxMDAwICAjIHBl"
        "ci1saXN0aW5nIGNlaWxpbmc7IHN0b3AgcGFnaW5hdGluZyB3aGVuIHJlYWNoZWQKCgpkZWYgX2xp"
        "c3RpbmcocGF0aCwgdG9rLCBxdW90YSwgKipwYXJhbXMpOgogICAgIiIiUGFnaW5hdGUgb25lIGxp"
        "c3RpbmcgdG8gaXRzIGNhcCwgeWllbGRpbmcgcG9zdCBkaWN0cy4KCiAgICBTdG9wcyBvbjogbm8g"
        "Y2hpbGRyZW4sIG5vIGBhZnRlcmAgY3Vyc29yLCBvciBMSVNUSU5HX0NBUCByZWFjaGVkLiBUaGUg"
        "Y2FwCiAgICBjaGVjayBpcyB3aGF0IGtlZXBzIHRoaXMgZnJvbSBzcGVuZGluZyBjYWxscyBvbiBw"
        "YWdlcyBSZWRkaXQgd2lsbCBub3QKICAgIHNlcnZlLiIiIgogICAgYWZ0ZXIsIHNlZW4gPSBOb25l"
        "LCAwCiAgICB3aGlsZSBzZWVuIDwgTElTVElOR19DQVA6CiAgICAgICAgcCA9IGRpY3QocGFyYW1z"
        "LCBsaW1pdD1QQUdFKQogICAgICAgIGlmIGFmdGVyOgogICAgICAgICAgICBwWyJhZnRlciJdID0g"
        "YWZ0ZXIKICAgICAgICBib2R5ID0gZ2V0KHBhdGgsIHRvaywgcXVvdGEsICoqcCkKICAgICAgICBp"
        "ZiBub3QgYm9keToKICAgICAgICAgICAgcmV0dXJuCiAgICAgICAgZGF0YSA9IGJvZHkuZ2V0KCJk"
        "YXRhIiwge30pCiAgICAgICAga2lkcyA9IGRhdGEuZ2V0KCJjaGlsZHJlbiIsIFtdKQogICAgICAg"
        "IGlmIG5vdCBraWRzOgogICAgICAgICAgICByZXR1cm4KICAgICAgICBmb3IgYyBpbiBraWRzOgog"
        "ICAgICAgICAgICB5aWVsZCBjLmdldCgiZGF0YSIsIHt9KQogICAgICAgIHNlZW4gKz0gbGVuKGtp"
        "ZHMpCiAgICAgICAgYWZ0ZXIgPSBkYXRhLmdldCgiYWZ0ZXIiKQogICAgICAgIGlmIG5vdCBhZnRl"
        "cjoKICAgICAgICAgICAgcmV0dXJuCgoKZGVmIGhhcnZlc3QodG9rLCBxdW90YSwgbW9udGhzLCB2"
        "ZXJib3NlPVRydWUsIGRlZXA9RmFsc2UsIG1heF9wb3N0cz1Ob25lKToKICAgICIiIldhbGsgdGhl"
        "IHBhcnRpdGlvbiBzcGFjZSwgeWllbGRpbmcgKG1vbnRoLCB0ZXh0KSAtIFRFWFQgT05MWS4KCiAg"
        "ICBQb3N0IGlkcyBhcmUgaGVsZCBpbiBtZW1vcnkgdG8gZGVkdXBsaWNhdGUgYW5kIHRvIGZldGNo"
        "IGNvbW1lbnQgdHJlZXMsIGFuZAogICAgYXJlIG5ldmVyIHlpZWxkZWQsIHdyaXR0ZW4gb3IgbG9n"
        "Z2VkLiBUaGUgY2FsbGVyIHJlY2VpdmVzIGJhcmUgc3RyaW5ncywgc28KICAgIG5vIHVzZXJuYW1l"
        "LCBpZCBvciBwZXJtYWxpbmsgY2FuIHJlYWNoIHRoZSBhbmFseXNlciBvciB0aGUgb3V0cHV0Lgog"
        "ICAgIiIiCiAgICBzaW5jZSA9IGR0LmRhdGV0aW1lLnV0Y25vdygpIC0gZHQudGltZWRlbHRhKGRh"
        "eXM9MzAgKiBtb250aHMpCiAgICB0ZXJtcyA9IERFRVBfVEVSTVMgaWYgZGVlcCBlbHNlIFNFQVJD"
        "SF9URVJNUwogICAgc29ydHMgPSBERUVQX1NPUlRTIGlmIGRlZXAgZWxzZSBbIm5ldyJdCiAgICB3"
        "aW5kb3dzID0gREVFUF9XSU5ET1dTIGlmIGRlZXAgZWxzZSBbImFsbCJdCgogICAgc2Vlbl9pZHMg"
        "PSBzZXQoKSAgICAgICMgZGVkdXBlIGFjcm9zcyBwYXJ0aXRpb25zOyBpbi1tZW1vcnkgb25seQog"
        "ICAgc3RhdHMgPSB7InF1ZXJpZXMiOiAwLCAicG9zdHNfcmF3IjogMCwgInBvc3RzX3VuaXF1ZSI6"
        "IDAsICJjb21tZW50cyI6IDAsCiAgICAgICAgICAgICAidG9vX29sZCI6IDB9CgogICAgZm9yIHN1"
        "YiBpbiBTVUJSRURESVRTOgogICAgICAgIGZvciB0ZXJtIGluIHRlcm1zOgogICAgICAgICAgICBm"
        "b3Igc29ydCBpbiBzb3J0czoKICAgICAgICAgICAgICAgIGZvciB3aW4gaW4gd2luZG93czoKICAg"
        "ICAgICAgICAgICAgICAgICBpZiBtYXhfcG9zdHMgYW5kIGxlbihzZWVuX2lkcykgPj0gbWF4X3Bv"
        "c3RzOgogICAgICAgICAgICAgICAgICAgICAgICBicmVhawogICAgICAgICAgICAgICAgICAgIHN0"
        "YXRzWyJxdWVyaWVzIl0gKz0gMQogICAgICAgICAgICAgICAgICAgIGZvciBkIGluIF9saXN0aW5n"
        "KGYiL3Ive3N1Yn0vc2VhcmNoIiwgdG9rLCBxdW90YSwgcT10ZXJtLAogICAgICAgICAgICAgICAg"
        "ICAgICAgICAgICAgICAgICAgICAgIHJlc3RyaWN0X3NyPTEsIHNvcnQ9c29ydCwgdD13aW4pOgog"
        "ICAgICAgICAgICAgICAgICAgICAgICBzdGF0c1sicG9zdHNfcmF3Il0gKz0gMQogICAgICAgICAg"
        "ICAgICAgICAgICAgICBwaWQgPSBkLmdldCgiaWQiKQogICAgICAgICAgICAgICAgICAgICAgICBp"
        "ZiBub3QgcGlkIG9yIHBpZCBpbiBzZWVuX2lkczoKICAgICAgICAgICAgICAgICAgICAgICAgICAg"
        "IGNvbnRpbnVlICAgICAgICAgICMgdW5pb24sIG5vdCBzdW0KICAgICAgICAgICAgICAgICAgICAg"
        "ICAgc2Vlbl9pZHMuYWRkKHBpZCkKICAgICAgICAgICAgICAgICAgICAgICAgc3RhdHNbInBvc3Rz"
        "X3VuaXF1ZSJdICs9IDEKICAgICAgICAgICAgICAgICAgICAgICAgY3JlYXRlZCA9IGR0LmRhdGV0"
        "aW1lLnV0Y2Zyb210aW1lc3RhbXAoZC5nZXQoImNyZWF0ZWRfdXRjIiwgMCkpCiAgICAgICAgICAg"
        "ICAgICAgICAgICAgIGlmIGNyZWF0ZWQgPCBzaW5jZToKICAgICAgICAgICAgICAgICAgICAgICAg"
        "ICAgIHN0YXRzWyJ0b29fb2xkIl0gKz0gMQogICAgICAgICAgICAgICAgICAgICAgICAgICAgY29u"
        "dGludWUKICAgICAgICAgICAgICAgICAgICAgICAgbW9udGggPSBjcmVhdGVkLnN0cmZ0aW1lKCIl"
        "WS0lbSIpCiAgICAgICAgICAgICAgICAgICAgICAgIHRleHQgPSAiICIuam9pbihmaWx0ZXIoTm9u"
        "ZSwgW2QuZ2V0KCJ0aXRsZSIpLCBkLmdldCgic2VsZnRleHQiKV0pKQogICAgICAgICAgICAgICAg"
        "ICAgICAgICBpZiB0ZXh0LnN0cmlwKCk6CiAgICAgICAgICAgICAgICAgICAgICAgICAgICB5aWVs"
        "ZCBtb250aCwgdGV4dAoKICAgICAgICAgICAgICAgICAgICAgICAgIyBUaGUgbXVsdGlwbGllci4g"
        "Q29tbWVudCB0cmVlcyBhcmUgbm90IHN1YmplY3QgdG8gdGhlCiAgICAgICAgICAgICAgICAgICAg"
        "ICAgICMgcG9zdC1saXN0aW5nIGNhcCwgYW5kIHRoaXMgaXMgd2hlcmUgdGFzdGUgdGFsayBpcy4K"
        "ICAgICAgICAgICAgICAgICAgICAgICAgY2JvZHkgPSBnZXQoZiIvci97c3VifS9jb21tZW50cy97"
        "cGlkfSIsIHRvaywgcXVvdGEsCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGxp"
        "bWl0PTUwMCwgZGVwdGg9Miwgc29ydD0idG9wIikKICAgICAgICAgICAgICAgICAgICAgICAgaWYg"
        "bm90IGNib2R5IG9yIGxlbihjYm9keSkgPCAyOgogICAgICAgICAgICAgICAgICAgICAgICAgICAg"
        "Y29udGludWUKICAgICAgICAgICAgICAgICAgICAgICAgZm9yIHQgaW4gX3dhbGtfY29tbWVudHMo"
        "Y2JvZHlbMV0uZ2V0KCJkYXRhIiwge30pLmdldCgiY2hpbGRyZW4iLCBbXSkpOgogICAgICAgICAg"
        "ICAgICAgICAgICAgICAgICAgc3RhdHNbImNvbW1lbnRzIl0gKz0gMQogICAgICAgICAgICAgICAg"
        "ICAgICAgICAgICAgeWllbGQgbW9udGgsIHQKICAgICAgICAgICAgICAgICAgICBpZiB2ZXJib3Nl"
        "OgogICAgICAgICAgICAgICAgICAgICAgICBwcmludChmIiAgci97c3VifSBxPXt0ZXJtIXJ9IHNv"
        "cnQ9e3NvcnR9IHQ9e3dpbn0gLT4gIgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICBmIntz"
        "dGF0c1sncG9zdHNfdW5pcXVlJ106LH0gdW5pcXVlIHBvc3RzLCAiCiAgICAgICAgICAgICAgICAg"
        "ICAgICAgICAgICAgIGYie3N0YXRzWydjb21tZW50cyddOix9IGNvbW1lbnRzIiwgZmx1c2g9VHJ1"
        "ZSkKICAgIGhhcnZlc3Quc3RhdHMgPSBzdGF0cwoKCmRlZiBfd2Fsa19jb21tZW50cyhjaGlsZHJl"
        "biwgZGVwdGg9MCk6CiAgICAiIiJZaWVsZCBjb21tZW50IGJvZGllcyBmcm9tIGEgdHJlZS4gU2tp"
        "cHMgYG1vcmVgIHN0dWJzIHJhdGhlciB0aGFuCiAgICBleHBhbmRpbmcgdGhlbTogZWFjaCBleHBh"
        "bnNpb24gaXMgYW5vdGhlciBjYWxsLCBhbmQgYXQgdGhpcyBjb3JwdXMgc2l6ZSB0aGUKICAgIG1h"
        "cmdpbmFsIGNvbW1lbnQgaXMgbm90IHdvcnRoIHRoZSBxdW90YS4gUmVjb3JkZWQgYXMgYSBrbm93"
        "biBsaW1pdGF0aW9uLiIiIgogICAgaWYgZGVwdGggPiA0OgogICAgICAgIHJldHVybgogICAgZm9y"
        "IGMgaW4gY2hpbGRyZW4gb3IgW106CiAgICAgICAgaWYgYy5nZXQoImtpbmQiKSAhPSAidDEiOgog"
        "ICAgICAgICAgICBjb250aW51ZSAgICAgICAgICAgICAgICAgICAgICAjIGBtb3JlYCBzdHVicyBh"
        "bmQgYW55dGhpbmcgbm9uLWNvbW1lbnQKICAgICAgICBkID0gYy5nZXQoImRhdGEiLCB7fSkKICAg"
        "ICAgICBib2R5ID0gZC5nZXQoImJvZHkiKQogICAgICAgIGlmIGJvZHkgYW5kIGJvZHkgbm90IGlu"
        "ICgiW2RlbGV0ZWRdIiwgIltyZW1vdmVkXSIpOgogICAgICAgICAgICB5aWVsZCBib2R5CiAgICAg"
        "ICAgcmVwbGllcyA9IGQuZ2V0KCJyZXBsaWVzIikKICAgICAgICBpZiBpc2luc3RhbmNlKHJlcGxp"
        "ZXMsIGRpY3QpOgogICAgICAgICAgICB5aWVsZCBmcm9tIF93YWxrX2NvbW1lbnRzKAogICAgICAg"
        "ICAgICAgICAgcmVwbGllcy5nZXQoImRhdGEiLCB7fSkuZ2V0KCJjaGlsZHJlbiIsIFtdKSwgZGVw"
        "dGggKyAxKQoKCiMgLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tLS0tLS0tLS0tIGFuYWx5c2VyIC0tCmRlZiBydW4obW9udGhzLCBsaW1pdD1Ob25l"
        "LCB2ZXJib3NlPVRydWUsIGRlZXA9RmFsc2UsIG1heF9wb3N0cz1Ob25lKToKICAgIHF1b3RhID0g"
        "UXVvdGEoKQogICAgdG9rID0gdG9rZW4oKQogICAgcm93cywgYnlfbW9udGggPSBbXSwgY29sbGVj"
        "dGlvbnMuQ291bnRlcigpCiAgICBmb3IgbW9udGgsIHRleHQgaW4gaGFydmVzdCh0b2ssIHF1b3Rh"
        "LCBtb250aHMsIHZlcmJvc2UsIGRlZXAsIG1heF9wb3N0cyk6CiAgICAgICAgcm93cy5hcHBlbmQo"
        "eyJjb21tZW50IjogdGV4dCwgIm1vbnRoIjogbW9udGh9KQogICAgICAgIGJ5X21vbnRoW21vbnRo"
        "XSArPSAxCiAgICAgICAgaWYgbGltaXQgYW5kIGxlbihyb3dzKSA+PSBsaW1pdDoKICAgICAgICAg"
        "ICAgYnJlYWsKICAgIHJlcyA9IGFuYWx5c2Uocm93cykgICAgICAgICAgICAgICAgICAgICAgIyBh"
        "Z2dyZWdhdGVzIG9ubHkKICAgIHJlc1sibW9udGhzIl0gPSBkaWN0KHNvcnRlZChieV9tb250aC5p"
        "dGVtcygpKSkKICAgIHJlc1sicXVvdGEiXSA9IHF1b3RhLnJlcG9ydCgpCiAgICByZXNbImhhcnZl"
        "c3QiXSA9IGdldGF0dHIoaGFydmVzdCwgInN0YXRzIiwge30pCiAgICByZXR1cm4gcmVzCgoKZGVm"
        "IHdyaXRlKHJlcywgbW9udGhzKToKICAgIG9zLm1ha2VkaXJzKE9VVF9ESVIsIGV4aXN0X29rPVRy"
        "dWUpCiAgICBzdGFtcCA9IGR0LmRhdGUudG9kYXkoKS5pc29mb3JtYXQoKQoKICAgIGZvciBuYW1l"
        "LCBrZXkgaW4gKCgiZmxhdm9yIiwgImZsYXZvcnMiKSwgKCJicmFuZCIsICJicmFuZHMiKSk6CiAg"
        "ICAgICAgcGF0aCA9IG9zLnBhdGguam9pbihPVVRfRElSLCBmIntuYW1lfV9wdWxzZV9hcGlfe3N0"
        "YW1wfS5jc3YiKQogICAgICAgIGltcG9ydCBjc3YgYXMgX2NzdgogICAgICAgIHdpdGggb3Blbihw"
        "YXRoLCAidyIsIG5ld2xpbmU9IiIsIGVuY29kaW5nPSJ1dGYtOCIpIGFzIGZoOgogICAgICAgICAg"
        "ICB3ID0gX2Nzdi5EaWN0V3JpdGVyKGZoLCBmaWVsZG5hbWVzPWxpc3QocmVzW2tleV1bMF0ua2V5"
        "cygpKSkKICAgICAgICAgICAgdy53cml0ZWhlYWRlcigpCiAgICAgICAgICAgIHcud3JpdGVyb3dz"
        "KHJlc1trZXldKQogICAgICAgIHByaW50KGYiICB3cm90ZSB7b3MucGF0aC5yZWxwYXRoKHBhdGgs"
        "IFJPT1QpfSAgKHtsZW4ocmVzW2tleV0pfSByb3dzKSIpCgogICAgbWV0YSA9IG9zLnBhdGguam9p"
        "bihPVVRfRElSLCBmIm1ldGFfYXBpX3tzdGFtcH0uY3N2IikKICAgIGltcG9ydCBjc3YgYXMgX2Nz"
        "dgogICAgd2l0aCBvcGVuKG1ldGEsICJ3IiwgbmV3bGluZT0iIiwgZW5jb2Rpbmc9InV0Zi04Iikg"
        "YXMgZmg6CiAgICAgICAgdyA9IF9jc3Yud3JpdGVyKGZoKQogICAgICAgIHcud3JpdGVyb3coWyJr"
        "ZXkiLCAidmFsdWUiXSkKICAgICAgICBmb3IgaywgdiBpbiBbCiAgICAgICAgICAgICgic291cmNl"
        "IiwgIlJlZGRpdCBEYXRhIEFQSSAob2F1dGgucmVkZGl0LmNvbSkiKSwKICAgICAgICAgICAgKCJt"
        "ZXRob2QiLCAiYXV0aGVudGljYXRlZCBPQXV0aCBzY3JpcHQgYXBwOyBubyBIVE1MLCBubyBjb29r"
        "aWVzIiksCiAgICAgICAgICAgICgic3VicmVkZGl0cyIsICJ8Ii5qb2luKFNVQlJFRERJVFMpKSwK"
        "ICAgICAgICAgICAgKCJzZWFyY2hfdGVybXMiLCAifCIuam9pbihTRUFSQ0hfVEVSTVMpKSwKICAg"
        "ICAgICAgICAgKCJtb250aHNfcmVxdWVzdGVkIiwgbW9udGhzKSwKICAgICAgICAgICAgKCJyb3dz"
        "X3NlZW4iLCByZXNbInJvd3Nfc2VlbiJdKSwKICAgICAgICAgICAgKCJyb3dzX21hdGNoZWQiLCBy"
        "ZXNbInJvd3NfbWF0Y2hlZCJdKSwKICAgICAgICAgICAgKCJtYXRjaF9yYXRlX3BjdCIsIHJlc1si"
        "bWF0Y2hfcmF0ZV9wY3QiXSksCiAgICAgICAgICAgICgic2VudGltZW50X2VuZ2luZSIsIHJlc1si"
        "ZW5naW5lIl0pLAogICAgICAgICAgICAoImFwaV9jYWxscyIsIHJlc1sicXVvdGEiXVsiY2FsbHMi"
        "XSksCiAgICAgICAgICAgICgiZ2VuZXJhdGVkX2F0IiwgZHQuZGF0ZXRpbWUudXRjbm93KCkuaXNv"
        "Zm9ybWF0KCkgKyAiWiIpLAogICAgICAgICAgICAoInByaXZhY3kiLCAiYWdncmVnYXRlcyBvbmx5"
        "OyBubyB1c2VybmFtZXMsIGlkcyBvciByYXcgdGV4dCBzdG9yZWQiKSwKICAgICAgICAgICAgKCJz"
        "YW1wbGluZyIsICJsaXN0aW5nIGVuZHBvaW50cyBjYXAgfjEwMDAgaXRlbXMvcXVlcnk7IGNvbnNp"
        "c3RlbnQgIgogICAgICAgICAgICAgICAgICAgICAgICAgInNhbXBsZSBwZXIgbW9udGgsIE5PVCBh"
        "IGNlbnN1cyIpLAogICAgICAgIF06CiAgICAgICAgICAgIHcud3JpdGVyb3coW2ssIHZdKQogICAg"
        "cHJpbnQoZiIgIHdyb3RlIHtvcy5wYXRoLnJlbHBhdGgobWV0YSwgUk9PVCl9IikKCgojIC0tLS0t"
        "LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0gbWFpbiAtLQpkZWYgcGxhbihkZWVwPUZhbHNlKToKICAgICIiIldoYXQgYSByZWFsIHJ1"
        "biB3b3VsZCBkbywgcHJpbnRlZCB3aXRob3V0IG1ha2luZyBhIHNpbmdsZSBjYWxsLiIiIgogICAg"
        "dGVybXMgPSBERUVQX1RFUk1TIGlmIGRlZXAgZWxzZSBTRUFSQ0hfVEVSTVMKICAgIHNvcnRzID0g"
        "REVFUF9TT1JUUyBpZiBkZWVwIGVsc2UgWyJuZXciXQogICAgd2lucyA9IERFRVBfV0lORE9XUyBp"
        "ZiBkZWVwIGVsc2UgWyJhbGwiXQogICAgcGFydHMgPSBsZW4oU1VCUkVERElUUykgKiBsZW4odGVy"
        "bXMpICogbGVuKHNvcnRzKSAqIGxlbih3aW5zKQogICAgY2FsbHMgPSBwYXJ0cwogICAgcHJpbnQo"
        "ZiIiIgpQTEFOIOKAlCBubyBuZXR3b3JrIGNhbGxzIG1hZGUgICBbeydERUVQJyBpZiBkZWVwIGVs"
        "c2UgJ3N0YW5kYXJkJ31dCgogIHN1YnJlZGRpdHMgICAgIHtsZW4oU1VCUkVERElUUyl9ICB7Jywg"
        "Jy5qb2luKCdyLycgKyB4IGZvciB4IGluIFNVQlJFRERJVFMpfQogIHF1ZXJ5IHRlcm1zICAgIHts"
        "ZW4odGVybXMpfQogIHNvcnRzICAgICAgICAgIHtsZW4oc29ydHMpfSAge3NvcnRzfQogIHRpbWUg"
        "d2luZG93cyAgIHtsZW4od2lucyl9ICB7d2luc30KICAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0KICBwYXJ0aXRpb25zICAg"
        "ICB7cGFydHM6LH0gIChzdWJyZWRkaXQgeCB0ZXJtIHggc29ydCB4IHdpbmRvdykKICBlYWNoIHBh"
        "Z2luYXRlcyB0byB0aGUge0xJU1RJTkdfQ0FQOix9LWl0ZW0gcGVyLWxpc3RpbmcgY2FwLCBzbyB0"
        "aGUgY2VpbGluZyBpcwogIHtwYXJ0cyAqIExJU1RJTkdfQ0FQOix9IHBvc3QtaGl0cyBiZWZvcmUg"
        "ZGVkdXBlIC0gdGhlIHVuaW9uIHdpbGwgYmUgZmFyIHNtYWxsZXIsCiAgYW5kIHRoYXQgdW5pb24g"
        "aXMgdGhlIG51bWJlciB0aGF0IG1hdHRlcnMuCgogIHNlYXJjaCBjYWxscyAgIHtwYXJ0czosfSAu"
        "LiB7cGFydHMgKiAoTElTVElOR19DQVAgLy8gUEFHRSk6LH0gICgxIHBlciBwYWdlLCB1cCB0byB7"
        "TElTVElOR19DQVAgLy8gUEFHRX0gcGFnZXMgZWFjaCkKICBjb21tZW50IGNhbGxzICAxIHBlciBV"
        "TklRVUUgcG9zdAogIHBhY2luZyAgICAgICAgIHtRUE1fQlVER0VUfSBxdWVyaWVzL21pbiAoe1NM"
        "RUVQOi4xZn1zIGFwYXJ0KQoKICBIT1cgVEhFIDEsMDAwIENBUCBJUyBCRUFURU4KICBUaGUgY2Fw"
        "IGlzIHBlciBsaXN0aW5nLCBub3QgcGVyIHN1YnJlZGRpdC4gRWFjaCBkaXN0aW5jdCAodGVybSwg"
        "c29ydCwgd2luZG93KQogIGlzIGl0cyBvd24gbGlzdGluZyB3aXRoIGl0cyBvd24ge0xJU1RJTkdf"
        "Q0FQOix9LiBUYWtpbmcgdGhlIHVuaW9uIGFjcm9zcyB7cGFydHM6LH0gb2YKICB0aGVtIGlzIG9y"
        "ZGluYXJ5IEFQSSB1c2UgLSBldmVyeSBjYWxsIGlzIGF1dGhlbnRpY2F0ZWQgYW5kIHJhdGUtbGlt"
        "aXRlZC4KICBDb21tZW50IHRyZWVzIGFyZSBub3Qgc3ViamVjdCB0byB0aGUgcG9zdCBjYXAgYXQg"
        "YWxsLCBhbmQgYXJlIHdoZXJlIG1vc3Qgb2YKICB0aGUgdGV4dCBjb21lcyBmcm9tLgoKICBXSEFU"
        "IElUIFNUSUxMIElTIE5PVAogIEEgY2Vuc3VzLiBSZWRkaXQncyBzZWFyY2ggaW5kZXggZG9lcyBu"
        "b3QgcmVsaWFibHkgc3VyZmFjZSB2ZXJ5IG9sZCBvcgogIGxvdy1lbmdhZ2VtZW50IHBvc3RzLCBz"
        "byBjb3ZlcmFnZSBkZWNheXMgd2l0aCBhZ2UgaW4gYSB3YXkgdGhpcyBjYW5ub3QKICBtZWFzdXJl"
        "IGZyb20gdGhlIGluc2lkZS4gUmVwb3J0IHdoYXQgd2FzIGNvbGxlY3RlZDsgbmV2ZXIgaW1wbHkg"
        "Y29tcGxldGVuZXNzLgoKICBXSEFUIElUIENPU1RTIElOIFRJTUUKICBQYWNpbmcgaXMgdGhlIGJp"
        "bmRpbmcgY29uc3RyYWludCwgbm90IHF1b3RhLiBBIG1vY2sgcnVuIG9mIHRoZSBzYW1lIGxvZ2lj"
        "CiAgKGNhcHN0b25lL3Rlc3RzL3Rlc3RfZGVlcF9oYXJ2ZXN0LnB5KSB0dXJuZWQgNDggcGFydGl0"
        "aW9ucyBpbnRvIH4yMSw3MDAKICB1bmlxdWUgcG9zdHMsIHNvIHRoaXMgcGxhbidzIHtwYXJ0czos"
        "fSBwYXJ0aXRpb25zIGFyZSBpbiB0aGUgdGVucyBvZgogIHRob3VzYW5kcyBvZiBwb3N0cyAtIGFu"
        "ZCBldmVyeSB1bmlxdWUgcG9zdCBjb3N0cyBvbmUgbW9yZSBjYWxsIGZvciBpdHMKICBjb21tZW50"
        "cy4gQXQge1FQTV9CVURHRVR9L21pbiB0aGF0IGlzIHJlYWxpc3RpY2FsbHkKICB7KHBhcnRzICsg"
        "MjAwMDApICogU0xFRVAgLyAzNjAwOi4wZn0teyhwYXJ0cyAqIDUgKyA0MDAwMCkgKiBTTEVFUCAv"
        "IDM2MDA6LjBmfSBIT1VSUyBmb3IgYSBmdWxsIHB1bGwuCgogIERvIGEgYm91bmRlZCBmaXJzdCBy"
        "dW4gaW5zdGVhZCwgbG9vayBhdCB3aGF0IGNvbWVzIGJhY2ssIHRoZW4gd2lkZW46CiAgICAgIC0t"
        "ZGVlcCAtLW1heC1wb3N0cyAyMDAwICAgICAgICAofnsoMjAwICsgMjAwMCkgKiBTTEVFUCAvIDYw"
        "Oi4wZn0gbWluKQogIFRoZSBjYWNoZSBtYWtlcyB0aGlzIGZyZWUgdG8gcmVzdW1lLCBzbyBhIGxv"
        "bmcgcnVuIGNhbiBiZSBzdG9wcGVkIGFuZAogIHJlc3RhcnRlZCB3aXRob3V0IGxvc2luZyB3b3Jr"
        "LgoKICBjYWNoZSAgICAgICAgICB7b3MucGF0aC5yZWxwYXRoKENBQ0hFX0RJUiwgUk9PVCl9ICAo"
        "cmUtcnVucyBmcmVlLCBpbnRlcnJ1cHRlZCBydW5zIHJlc3VtZSkKICB2b2NhYnVsYXJ5ICAgICB7"
        "bGVuKEZMQVZPUl9BTElBU0VTKX0gZmxhdm9ycyAvIHtsZW4oQlJBTkRfQUxJQVNFUyl9IGJyYW5k"
        "cwogIHdyaXRlcyAgICAgICAgIGRhdGEvcmVkZGl0L2ZsYXZvcl9wdWxzZV9hcGlfPGRhdGU+LmNz"
        "diwgYnJhbmRfLi4uLCBtZXRhXy4uLgogIG5ldmVyIHdyaXRlcyAgIHVzZXJuYW1lcywgcG9zdCBp"
        "ZHMsIHBlcm1hbGlua3MsIG9yIHJhdyBjb21tZW50IHRleHQKCkNSRURFTlRJQUxTICB7J3ByZXNl"
        "bnQnIGlmIG9zLmVudmlyb24uZ2V0KCdSRURESVRfQ0xJRU5UX0lEJykgZWxzZSAnTk9UIFNFVCDi"
        "gJQgYSByZWFsIHJ1biB3aWxsIHN0b3AgYW5kIHRlbGwgeW91IGhvdyd9ClRFUk1TICAgICAgICBy"
        "ZWFkIGNhcHN0b25lL1JFRERJVF9BUElfVEVSTVMubWQgYmVmb3JlIHRoZSBmaXJzdCByZWFsIHJ1"
        "bgoiIiIpCgoKZGVmIG1haW4oKToKICAgIGFwID0gYXJncGFyc2UuQXJndW1lbnRQYXJzZXIoZGVz"
        "Y3JpcHRpb249X19kb2NfXy5zcGxpdGxpbmVzKClbMF0pCiAgICBhcC5hZGRfYXJndW1lbnQoIi0t"
        "ZHJ5LXJ1biIsIGFjdGlvbj0ic3RvcmVfdHJ1ZSIsIGhlbHA9InByaW50IHRoZSBwbGFuLCBjYWxs"
        "IG5vdGhpbmciKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLW1vbnRocyIsIHR5cGU9aW50LCBkZWZh"
        "dWx0PTI0LCBoZWxwPSJob3cgZmFyIGJhY2sgKGRlZmF1bHQgMjQpIikKICAgIGFwLmFkZF9hcmd1"
        "bWVudCgiLS1saW1pdCIsIHR5cGU9aW50LCBoZWxwPSJzdG9wIGFmdGVyIE4gdGV4dHMgKGZvciBh"
        "IGNoZWFwIGZpcnN0IGxvb2spIikKICAgIGFwLmFkZF9hcmd1bWVudCgiLS1kZWVwIiwgYWN0aW9u"
        "PSJzdG9yZV90cnVlIiwKICAgICAgICAgICAgICAgICAgICBoZWxwPSJwYXJ0aXRpb24gYWNyb3Nz"
        "IHRlcm1zIHggc29ydHMgeCB0aW1lIHdpbmRvd3MgdG8gZ2V0ICIKICAgICAgICAgICAgICAgICAg"
        "ICAgICAgICJwYXN0IHRoZSAxLDAwMC1pdGVtIHBlci1saXN0aW5nIGNhcCIpCiAgICBhcC5hZGRf"
        "YXJndW1lbnQoIi0tbWF4LXBvc3RzIiwgdHlwZT1pbnQsCiAgICAgICAgICAgICAgICAgICAgaGVs"
        "cD0ic3RvcCBvbmNlIHRoaXMgbWFueSBVTklRVUUgcG9zdHMgaGF2ZSBiZWVuIHNlZW4iKQogICAg"
        "YXAuYWRkX2FyZ3VtZW50KCItLXF1aWV0IiwgYWN0aW9uPSJzdG9yZV90cnVlIikKICAgIGEgPSBh"
        "cC5wYXJzZV9hcmdzKCkKCiAgICBpZiBhLmRyeV9ydW46CiAgICAgICAgcGxhbihhLmRlZXApCiAg"
        "ICAgICAgcmV0dXJuCgogICAgcmVzID0gcnVuKGEubW9udGhzLCBhLmxpbWl0LCB2ZXJib3NlPW5v"
        "dCBhLnF1aWV0LCBkZWVwPWEuZGVlcCwKICAgICAgICAgICAgICBtYXhfcG9zdHM9YS5tYXhfcG9z"
        "dHMpCiAgICBoID0gcmVzLmdldCgiaGFydmVzdCIsIHt9KQogICAgcHJpbnQoZiJcbiAge3Jlc1sn"
        "cm93c19zZWVuJ106LH0gdGV4dHMsIHtyZXNbJ3Jvd3NfbWF0Y2hlZCddOix9IG1hdGNoZWQgIgog"
        "ICAgICAgICAgZiIoe3Jlc1snbWF0Y2hfcmF0ZV9wY3QnXX0lKSAgwrcgIHtyZXNbJ3F1b3RhJ11b"
        "J2NhbGxzJ119IEFQSSBjYWxscyIpCiAgICBpZiBoOgogICAgICAgICMgUHJpbnRlZCBiZWNhdXNl"
        "IGl0IGlzIHRoZSBudW1iZXIgdGhhdCBhbnN3ZXJzICJkaWQgd2UgZ2V0IHBhc3QgMSwwMDAiOgog"
        "ICAgICAgICMgcG9zdHNfcmF3IGNvdW50cyBldmVyeSBoaXQgYWNyb3NzIHBhcnRpdGlvbnMsIHBv"
        "c3RzX3VuaXF1ZSBjb3VudHMgdGhlCiAgICAgICAgIyB1bmlvbi4gSWYgdW5pcXVlIGlzIHN0dWNr"
        "IG5lYXIgMSwwMDAgdGhlIHBhcnRpdGlvbmluZyBpcyBub3Qgd29ya2luZy4KICAgICAgICBwcmlu"
        "dChmIiAge2hbJ3F1ZXJpZXMnXX0gcGFydGl0aW9ucyDCtyB7aFsncG9zdHNfcmF3J106LH0gaGl0"
        "cyAtPiAiCiAgICAgICAgICAgICAgZiJ7aFsncG9zdHNfdW5pcXVlJ106LH0gVU5JUVVFIHBvc3Rz"
        "ICIKICAgICAgICAgICAgICBmIih7aFsncG9zdHNfcmF3J10gLSBoWydwb3N0c191bmlxdWUnXTos"
        "fSBkdXBsaWNhdGVzIGFjcm9zcyAiCiAgICAgICAgICAgICAgZiJwYXJ0aXRpb25zKSDCtyB7aFsn"
        "Y29tbWVudHMnXTosfSBjb21tZW50cyIpCiAgICB3cml0ZShyZXMsIGEubW9udGhzKQoKCmlmIF9f"
        "bmFtZV9fID09ICJfX21haW5fXyI6CiAgICBtYWluKCkK"
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
             f"1. Create {env_path} with these three lines:\n"
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

    # -- 3. writer ----------------------------------------------------------
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

    n = load_dotenv(os.path.join(HERE, ".env"))
    if n:
        print(f"  loaded {n} variable(s) from capstone/.env")

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
