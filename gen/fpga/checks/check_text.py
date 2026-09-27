#!/usr/bin/env python3
"""No label wider than the box it sits in.  Nothing here can render a font,
so the width is estimated from Helvetica's own advance widths, which are a
little wider than Archivo's --- so this over-estimates, and a label it does
not flag is safe."""
import os, re, sys, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_geom import arch, boxes
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'pages', 'fpga')
W = {' ':278,'!':278,'"':355,'#':556,'$':556,'%':889,'&':667,"'":191,'(':333,')':333,
     '*':389,'+':584,',':278,'-':333,'.':278,'/':278,':':278,';':278,'<':584,'=':584,
     '>':584,'?':556,'@':1015,'[':278,'\\':278,']':278,'^':469,'_':556,'`':333,
     '{':334,'|':260,'}':334,'~':584,'—':1000,'’':191,'×':584,' ':278}
for c, w in zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                [667,667,722,722,667,611,778,722,278,500,667,556,833,722,778,667,778,
                 722,667,611,722,667,944,667,667,611]): W[c] = w
for c, w in zip('abcdefghijklmnopqrstuvwxyz',
                [556,556,500,556,556,278,556,556,222,222,500,222,833,556,556,556,556,
                 333,500,278,556,500,722,500,500,500]): W[c] = w
for c in '0123456789': W[c] = 556
SIZE = {'d-t': 13, 'd-s': 11, 'd-m': 13, 'd-n': 11}

def width(s, cls):
    size = SIZE[cls.split()[0]]
    mono = cls.split()[0] in ('d-m', 'd-n')
    if mono: return len(s) * size * 0.6
    return sum(W.get(c, 556) for c in s) / 1000.0 * size

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
