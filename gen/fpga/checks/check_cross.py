#!/usr/bin/env python3
"""Two more geometric readings of the architecture drawing, each meant to be
compared between the base and the new pages rather than read alone:
  - segments of two different lines that cross away from their ends;
  - a segment that passes through the inside of a box it does not touch."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_geom import arch, boxes, polylines, EPS

def segs(pls):
    out = []
    for i, subs in enumerate(pls):
        for sub in subs:
            for a, b in zip(sub, sub[1:]):
                out.append((i, a, b))
    return out

def cross(a1, a2, b1, b2):
    def d(p, q, r): return (q[0]-p[0])*(r[1]-p[1]) - (q[1]-p[1])*(r[0]-p[0])
    d1, d2, d3, d4 = d(b1,b2,a1), d(b1,b2,a2), d(a1,a2,b1), d(a1,a2,b2)
    return ((d1 > EPS and d2 < -EPS) or (d1 < -EPS and d2 > EPS)) and \
           ((d3 > EPS and d4 < -EPS) or (d3 < -EPS and d4 > EPS))

def read(d, f):
    t = open(os.path.join(d, f + '.html')).read()
    g = arch(t)
    return boxes(g), polylines(g)

def report(d, f):
    bs, pls = read(d, f)
    ss = segs(pls)
    xs = set()
    for i in range(len(ss)):
        for j in range(i+1, len(ss)):
            if ss[i][0] == ss[j][0]: continue
            if cross(ss[i][1], ss[i][2], ss[j][1], ss[j][2]):
                xs.add(tuple(sorted([ss[i][1:], ss[j][1:]])))
    thru = set()
    for _, a, b in ss:
        for cls, x0, y0, x1, y1 in bs:
            if 'd-dot' in cls or 'd-plate' in cls: continue
            if x1-x0 > 1000 or y1-y0 > 400: continue      # the part's own outline
            for k in range(1, 40):
                t_ = k/40.0
                px, py = a[0]+(b[0]-a[0])*t_, a[1]+(b[1]-a[1])*t_
                if x0+EPS < px < x1-EPS and y0+EPS < py < y1-EPS:
                    thru.add((cls, x0, y0, x1, y1, a, b)); break
    return xs, thru

base = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'base')
new  = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'pages', 'fpga')
bad = 0
for f in ('arty-z7-20', 'cora-z7-07s'):
    bx, bt = report(base, f)
    nx, nt = report(new, f)
    print('%-13s crossings %d -> %d, lines through a box %d -> %d' % (f, len(bx), len(nx), len(bt), len(nt)))
    for c in sorted(nx - bx): print('   NEW crossing', c); bad += 1
    for c in sorted(nt - bt, key=str): print('   NEW through', c); bad += 1
    for c in sorted(bx - nx): print('   gone crossing', c)
    for c in sorted(bt - nt, key=str): print('   gone through', c)
print('crossings:', 'no new ones' if not bad else '%d new' % bad)
sys.exit(1 if bad else 0)
