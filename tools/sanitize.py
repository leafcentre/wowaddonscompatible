#!/usr/bin/env python3
"""Copy the live wowaddonscompatible skill into this repo with machine-specific
details replaced by placeholders.

The scrub map (real paths/ports/names) is deliberately NOT in this repo -- it is
read from $HOME/.wow-skill-scrub.json or the path given by --map, so the repo
never contains what it is scrubbing.

Usage:
  python tools/sanitize.py --src <live skill dir> --dst <repo dir> [--map FILE]

Exits non-zero if any forbidden pattern survives in the output.
"""
import argparse
import json
import os
import pathlib
import shutil
import sys

FILES = ['SKILL.md', 'references/12x-api-replacements.md',
         'references/live-client-measurement.md']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--dst', required=True)
    ap.add_argument('--map', default=os.path.join(os.path.expanduser('~'), '.wow-skill-scrub.json'))
    a = ap.parse_args()

    m = json.loads(pathlib.Path(a.map).read_text(encoding='utf-8'))
    src, dst = pathlib.Path(a.src), pathlib.Path(a.dst)

    bad = []
    for rel in FILES:
        t = (src / rel).read_text(encoding='utf-8')
        for old, new in m['replacements']:
            t = t.replace(old, new)
        for f in m.get('forbidden_patterns', []):
            if f in t:
                bad.append((rel, f))
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        # keep the repo LF-only so diffs stay clean
        out.write_bytes(t.replace('\r\n', '\n').encode('utf-8'))
        print('sanitized', rel, len(t), 'chars')

    if bad:
        for rel, f in bad:
            print('LEAK: %s still contains %r' % (rel, f), file=sys.stderr)
        return 1
    print('OK: no forbidden patterns in', len(FILES), 'files')
    return 0


if __name__ == '__main__':
    sys.exit(main())
