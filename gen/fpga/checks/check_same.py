#!/usr/bin/env python3
"""The three architecture drawings are one drawing: every difference between
the Arty Z7-20's and another's should be a difference somebody meant.  This
lists the geometry each page has that the Arty Z7-20 does not, and the other
way round, ignoring the text in a label and the class on a box."""
import os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_geom import arch
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'pages', 'fpga')

def shapes(f):
    g = arch(open(os.path.join(D, f + '.html')).read())
    g = re.sub(r'<!--.*?-->', '', g, flags=re.S)
    out = collections.Counter()
    for m in re.finditer(r'<rect[^>]*?x="(-?[\d.]+)" y="(-?[\d.]+)" width="([\d.]+)" height="([\d.]+)"', g):
        out['rect %s' % (m.groups(),)] += 1
    for m in re.finditer(r'<(?:path|line)[^>]*?(?:d="([^"]+)"|x1="(-?[\d.]+)" y1="(-?[\d.]+)" x2="(-?[\d.]+)" y2="(-?[\d.]+)")', g):
        out['line %s' % (m.groups(),)] += 1
    for m in re.finditer(r'<text[^>]*? x="(-?[\d.]+)" y="(-?[\d.]+)"', g):
        out['text %s,%s' % m.groups()] += 1
    for m in re.finditer(r'<tspan x="(-?[\d.]+)" y="(-?[\d.]+)"', g):
        out['tspan %s,%s' % m.groups()] += 1
    for m in re.finditer(r'<circle[^>]*?cx="(-?[\d.]+)" cy="(-?[\d.]+)" r="([\d.]+)"', g):
        out['circle %s,%s,%s' % m.groups()] += 1
    return out

a = shapes('arty-z7-20')
for f in ('cora-z7-07s',):
    b = shapes(f)
    print('=== %s against arty-z7-20' % f)
    for k in sorted((b - a).elements()): print('   only here : %s' % k)
    for k in sorted((a - b).elements()): print('   only Arty : %s' % k)
