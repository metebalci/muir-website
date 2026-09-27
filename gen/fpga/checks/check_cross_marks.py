#!/usr/bin/env python3
"""Every red cross sits on the corners of the box it marks, and every box
that says it is absent carries one."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_geom import arch
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'pages', 'fpga')
bad = 0
for f in ('arty-z7-20', 'cora-z7-07s'):
    g = arch(open(os.path.join(D, f + '.html')).read())
    rects = [tuple(map(float, m.groups())) for m in
             re.finditer(r'<rect class="d-box d-absent" x="(-?[\d.]+)" y="(-?[\d.]+)" width="([\d.]+)" height="([\d.]+)"', g)]
    marks = []
    for m in re.finditer(r'<path class="d-absent-x" d="M(-?[\d.]+),(-?[\d.]+) L(-?[\d.]+),(-?[\d.]+) M(-?[\d.]+),(-?[\d.]+) L(-?[\d.]+),(-?[\d.]+)"', g):
        v = list(map(float, m.groups()))
        marks.append((min(v[0], v[2]), min(v[1], v[3]), max(v[0], v[2]), max(v[1], v[3])))
    boxes = set((x, y, x + w, y + h) for x, y, w, h in rects)
    for b in sorted(boxes):
        if b not in [tuple(m) for m in marks]:
            print('%s: box %s has no cross on its corners' % (f, b)); bad += 1
    for m in marks:
        if tuple(m) not in boxes:
            print('%s: cross %s is on no absent box' % (f, m)); bad += 1
    print('%-13s %d absent boxes, %d crosses' % (f, len(boxes), len(marks)))
print('crosses:', 'OK' if not bad else '%d problem(s)' % bad)
sys.exit(1 if bad else 0)
