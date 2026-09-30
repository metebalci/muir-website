#!/usr/bin/env python3
"""No label wider than the box it sits in.  Nothing here can render a font,
so the width is computed from Plex Mono's advance, which is 600 units to the
em at every size and weight the drawings use, so a label of n letters at s
units is n * 0.6 * s units wide, and this is exact rather than an estimate.
Only centered labels are looked at, in the generated pages, where gen/fpga/fit.py
has already set the labels again where it could."""
import os, re, sys, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_geom import arch, boxes
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'pages', 'fpga')
SIZE = {'d-t': 13, 'd-s': 11, 'd-m': 13, 'd-n': 11, 'd-x': 9.5}

def width(s, cls):
    return len(s) * 0.6 * SIZE[cls.split()[0]]

def run(f):
    g = arch(open(os.path.join(D, f + '.html')).read())
    bs = [b for b in boxes(g) if 'd-plate' not in b[0]]
    worst = []
    for m in re.finditer(r'<text class="(d-[a-z-]+(?: d-[a-z-]+)*)" x="(-?[\d.]+)" y="(-?[\d.]+)" text-anchor="middle">([^<]*)</text>', g):
        cls, x, y, s = m.group(1), float(m.group(2)), float(m.group(3)), html.unescape(m.group(4))
        inner = None
        for c, x0, y0, x1, y1 in bs:
            if x0 <= x <= x1 and y0 - 2 <= y <= y1 + 2:
                if inner is None or (x1 - x0) < (inner[3] - inner[1]): inner = (c, x0, y0, x1, y1)
        if not inner: continue
        bw = inner[3] - inner[1]
        tw = width(s, cls)
        worst.append((tw / bw, s, round(tw, 1), bw, f))
    return worst

allw = []
for f in ('arty-z7-20', 'cora-z7-07s'):
    allw += run(f)
allw.sort(reverse=True)
seen = set()
for r, s, tw, bw, f in allw:
    if s in seen: continue
    seen.add(s)
    if r > 0.90:
        print('%-13s %5.2f of the box  %-42s (%.0f of %.0f)' % (f, r, s[:42], tw, bw))
print('the widest label uses %.0f%% of its box' % (allw[0][0] * 100))
