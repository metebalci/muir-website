#!/usr/bin/env python3
"""The lamps on every architecture drawing, read geometrically:
  - every lamp's label starts on its circle's line, 4 below its center and
    14 to its right, and every line of the lamps' box is a lamp's first line
    or the next line of the label above it, 14 lower;
  - no label runs into the next lamp's, and none past the box's foot;
  - every halo is around a lamp;
and against a table: each drawing has the lamps named below, in this order,
each in the color it lights on the board (muir-fpga's board tops: green,
red or blue; dark where the top leaves it unlit; absent where the board has
no lamp for that signal)."""
import html, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_geom import boxes, drawings
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'pages', 'fpga')
COLOR = {'#2da44e': 'green', '#d1495b': 'red', '#0969da': 'blue', 'none': 'dark'}
G, R, B, DARK, ABSENT = 'green', 'red', 'blue', 'dark', 'absent'
# muir-fpga: boards/arty-z7-20/cadr_arty.sv (LD4 red at an error halt, LD5
# blue for PROMENABLE) and quux15_arty.sv (LD4 red, LD5 dark);
# boards/kria-kr260/ (UF1, UF2);
# boards/de25-nano/ (every LEDR green; quux15_de25.sv: LEDR5 dark, LEDR6
# the memory port open).  cadr_de25.sv's LEDR6 is not drawn on the CADR's.
EXPECT = {
    'arty-z7-20': [('LD0', G), ('LD1', G), ('LD2', G), ('LD3', G), ('LD4', R), ('LD5', B)],
    'arty-z7-20 quux': [('LD0', G), ('LD1', G), ('LD2', G), ('LD3', G), ('LD4', R), ('LD5', DARK)],
    'kria-kr260': [('UF1', G), ('UF2', G)],
    'kria-kr260 quux': [('UF1', G), ('UF2', G)],
    'de25-nano': [('LEDR%d' % n, G) for n in range(6)],
    'de25-nano quux': [('LEDR%d' % n, G) for n in range(5)] + [('LEDR5', DARK), ('LEDR6', G)],
}
STEP, BELOW, RIGHT = 14, 4, 14
CIRCLE = re.compile(r'<circle\b([^>]*)/>')

def attr(a, k):
    m = re.search(r'\b%s="([^"]*)"' % k, a)
    return m.group(1) if m else None

bad = 0
for f, g in drawings(D):
    lamps, halos = [], []
    for m in CIRCLE.finditer(g):
        a = m.group(1)
        cx, cy, r = float(attr(a, 'cx')), float(attr(a, 'cy')), float(attr(a, 'r'))
        if r == 8:
            halos.append((cx, cy)); continue
        cls = attr(a, 'class') or ''
        color = ABSENT if 'd-absent' in cls.split() else COLOR.get(attr(a, 'fill'), attr(a, 'fill'))
        lamps.append((cy, cx, color))
    lamps.sort()
    problems = []
    for h in halos:
        if not any((cx, cy) == h for cy, cx, _ in lamps):
            problems.append('halo at %s is around no lamp' % (h,))
    # the lamps' box: the smallest box holding every lamp
    holding = [b for b in boxes(g) if all(b[1] < cx < b[3] and b[2] < cy < b[4] for cy, cx, _ in lamps)]
    if not lamps or not holding:
        problems.append('no lamps, or no box holding them all')
        box = None
    else:
        box = min(holding, key=lambda b: (b[3] - b[1]) * (b[4] - b[2]))
    texts = []
    if box:
        for m in re.finditer(r'<text class="[^"]*" x="(-?[\d.]+)" y="(-?[\d.]+)"[^>]*>([^<]*)</text>', g):
            x, y = float(m.group(1)), float(m.group(2))
            if box[1] < x < box[3] and box[2] < y < box[4]:
                texts.append((y, x, html.unescape(m.group(3))))
        texts.sort()
    first = {}
    for cy, cx, color in lamps:
        t = [s for s in texts if s[0] == cy + BELOW and s[1] == cx + RIGHT]
        if len(t) != 1:
            near = [s for s in texts if s[1] == cx + RIGHT and abs(s[0] - cy - BELOW) < 2 * STEP]
            problems.append('lamp at y %g: no label on its line (y %g); nearest %s' % (cy, cy + BELOW, near[:1]))
        else:
            first[t[0][0]] = (cy, color)
    labels, cur = [], None
    for y, x, s in texts:
        if y in first:
            cur = [y, y, s, first[y][1]]
            labels.append(cur)
        elif cur is not None and y == cur[1] + STEP:
            cur[1] = y
            cur[2] += ' ' + s
        else:
            problems.append('line "%s" at y %g is no lamp\'s label' % (s, y))
    for a, b in zip(labels, labels[1:]):
        if b[0] - a[1] < STEP:
            problems.append('"%s" runs into "%s"' % (a[2], b[2]))
    if labels and box and labels[-1][1] > box[4] - 4:
        problems.append('"%s" runs past the box\'s foot' % labels[-1][2])
    got = [(s.split(' —')[0] if '—' in s else None, color) for _, _, s, color in labels]
    if got != EXPECT[f]:
        problems.append('lamps %s, wanted %s' % (got, EXPECT[f]))
    for p in problems:
        print('%s: %s' % (f, p))
    bad += len(problems)
    print('%-16s %d lamps, %d halos, %d labels: %s' % (f, len(lamps), len(halos), len(labels),
          ', '.join('%s %s' % (n or '-', c) for n, c in got)))
print('lamps:', 'OK' if not bad else '%d problem(s)' % bad)
sys.exit(1 if bad else 0)
