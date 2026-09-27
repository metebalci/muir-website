#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""pages/ is what gen/build.py writes, byte for byte.

    python3 checks/generated.py [--root DIR]

Builds the whole site from src/ and gen/ into a scratch directory and
compares every page it writes with the one in pages/.  A page edited by
hand, or a change to the generator or to src/ that was not built, fails;
so does a built page that pages/ lacks, and a page in pages/ that is
neither built nor one of the two full-size image pages.  It exits 1 on any difference."""
import argparse, os, subprocess, sys, tempfile

# The two pages that are pages/ files of their own and not built.
STANDALONE = {'simulator/lashup.html', 'simulator/system-100.html'}


def check(root):
    problems = []
    with tempfile.TemporaryDirectory() as out:
        r = subprocess.run([sys.executable, '-B', os.path.join(root, 'gen', 'build.py'), out],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return ['gen/build.py failed:\n' + r.stderr]
        written = set(r.stdout.split())
        for dp, _, fs in os.walk(os.path.join(root, 'pages')):
            for f in fs:
                rel = os.path.relpath(os.path.join(dp, f), os.path.join(root, 'pages'))
                if f.endswith('.html') and rel not in written and rel not in STANDALONE:
                    problems.append('pages/%s: a page gen/build.py does not write' % rel)
        for rel in sorted(written):
            built = open(os.path.join(out, rel), 'rb').read()
            p = os.path.join(root, 'pages', rel)
            if not os.path.exists(p):
                problems.append('pages/%s: built, and not in pages/' % rel)
            elif open(p, 'rb').read() != built:
                problems.append('pages/%s: differs from what gen/build.py writes' % rel)
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    a = ap.parse_args()
    problems = check(a.root)
    for p in problems:
        print(p)
    print('generated: %d page%s differ%s' % (len(problems), '' if len(problems) == 1 else 's', 's' if len(problems) == 1 else ''))
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
