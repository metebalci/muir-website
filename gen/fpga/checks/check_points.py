#!/usr/bin/env python3
"""No coordinate moved: the set of points the drawing's lines are drawn
through is the same before and after, and every point in a split path was
already a point in the path it came out of."""
import os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_geom import arch
A, B = sys.argv[1], sys.argv[2]
def pts(d, f):
    g = arch(open(os.path.join(d, f + '.html')).read())
    c = collections.Counter()
    for m in re.finditer(r'<(?:path|line)[^>]*?d="([^"]+)"', g):
        for p in re.finditer(r'[MLml]\s*(-?[\d.]+),(-?[\d.]+)', m.group(1)):
            c[(float(p.group(1)), float(p.group(2)))] += 1
    for m in re.finditer(r'<line[^>]*?x1="(-?[\d.]+)" y1="(-?[\d.]+)" x2="(-?[\d.]+)" y2="(-?[\d.]+)"', g):
        c[(float(m.group(1)), float(m.group(2)))] += 1
        c[(float(m.group(3)), float(m.group(4)))] += 1
    return c
bad = 0
for f in ('arty-z7-20', 'cora-z7-07s'):
    a, b = pts(A, f), pts(B, f)
    new = set(b) - set(a); gone = set(a) - set(b)
    extra = {k: b[k]-a[k] for k in b if b[k] > a.get(k, 0)}
    fewer = {k: a[k]-b[k] for k in a if a[k] > b.get(k, 0)}
    print('%-13s points %d -> %d, new values %s, values gone %s' % (f, sum(a.values()), sum(b.values()), sorted(new) or 'none', sorted(gone) or 'none'))
    if extra: print('   repeated more often (a split at a point already there): %s' % extra)
    if fewer: print('   repeated less often: %s' % fewer); bad += 1
    if new or gone: bad += 1
print('coordinates:', 'nothing moved' if not bad else '%d problem(s)' % bad)
sys.exit(1 if bad else 0)
