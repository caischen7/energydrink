#!/usr/bin/env python3
"""Bundle the Reddit collector into ONE portable file.

    python capstone/scripts/build_standalone.py
    -> capstone/dist/reddit_deep_standalone.py

WHY GENERATED AND NOT HAND-WRITTEN
----------------------------------
run_reddit_deep.py needs three sibling modules, so on its own - dropped on a
Desktop, say - it fails with ModuleNotFoundError. The obvious fix is to paste
the modules into one file by hand. That is exactly how this project's flavor
rules drifted before: a hand-copy got cherry and mango wrong and silently
disagreed with every other page (see CLAUDE.md).

So the bundle is BUILT from the real sources every time. There is one
definition of every rule; this just packages it. Re-run after changing any
collector module and the bundle picks the change up.

HOW IT WORKS
    Each dependency's source is embedded base64-encoded (base64 so no quoting
    or escaping can corrupt it), then registered in sys.modules before the
    runner executes. The runner's own `import reddit_collector` then resolves
    against the embedded copy instead of the filesystem, and its sys.path
    manipulation becomes a harmless no-op.

The result is stdlib-only and runs anywhere Python 3.8+ does.
"""
import base64
import datetime as dt
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "capstone/dist/reddit_deep_standalone.py")

# Order matters: each is registered before anything that imports it.
MODULES = [
    ("classify_target_consumers", "data/scripts/classify_target_consumers.py"),
    ("flavor_mentions", "capstone/collectors/flavor_mentions.py"),
    ("reddit_collector", "capstone/collectors/reddit_collector.py"),
]
RUNNER = "capstone/run_reddit_deep.py"

PROLOGUE = '''#!/usr/bin/env python3
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
#  Built {stamp} from {commit}
#  Source of truth: capstone/collectors/ in the repo. Edit there, then rerun
#  capstone/scripts/build_standalone.py - edits made here are lost on rebuild.
# ===========================================================================
import base64 as _b64, sys as _sys, types as _types

_EMBEDDED = {{
{payload}
}}

def _install(name):
    """Register an embedded module so normal `import name` finds it."""
    mod = _types.ModuleType(name)
    mod.__file__ = f"<embedded:{{name}}>"
    mod.__package__ = ""
    _sys.modules[name] = mod
    exec(compile(_b64.b64decode(_EMBEDDED[name]).decode("utf-8"),
                 mod.__file__, "exec"), mod.__dict__)
    return mod

for _n in {order!r}:
    _install(_n)

# --------------------------------------------------------------------------
# Below: capstone/run_reddit_deep.py, verbatim.
# --------------------------------------------------------------------------
'''


def main():
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                                capture_output=True, text=True).stdout.strip() or "unknown"
    except OSError:
        commit = "unknown"

    payload, order = [], []
    for name, rel in MODULES:
        src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        b64 = base64.b64encode(src.encode("utf-8")).decode("ascii")
        # wrapped so the generated file stays readable in an editor
        chunks = [b64[i:i + 76] for i in range(0, len(b64), 76)]
        joined = "\n".join(f'        "{c}"' for c in chunks)
        payload.append(f'    "{name}": (\n{joined}\n    ),')
        order.append(name)

    runner = open(os.path.join(ROOT, RUNNER), encoding="utf-8").read()
    # The runner's sys.path lines are pointless once modules are embedded, and
    # actively confusing in a file sitting on someone's Desktop. Neutralised
    # rather than deleted, so the diff against the source stays obvious.
    runner = runner.replace(
        'sys.path.insert(0, os.path.join(HERE, "collectors"))',
        '# (bundled: modules are embedded above, no path setup needed)')
    runner = runner.replace(
        'sys.path.insert(0, os.path.join(ROOT, "data", "scripts"))', '')

    out = PROLOGUE.format(stamp=dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                          commit=commit, payload="\n".join(payload),
                          order=order) + runner

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(out)
    os.chmod(OUT, 0o755)
    print(f"wrote {os.path.relpath(OUT, ROOT)}  ({len(out)/1024:.0f} KB, "
          f"{len(order)} modules embedded, from {commit})")


if __name__ == "__main__":
    main()
