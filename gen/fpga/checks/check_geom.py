#!/usr/bin/env python3
"""No line on the architecture drawing ends in mid-air: every end of every
line lies on a box's edge or on another line.  And no two boxes overlap
except where one plainly contains the other."""
import os, re, sys
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'pages', 'fpga')
EPS = 0.75

def arch(t):
    """The architecture drawing's own <g>, which is one coordinate space."""
    i = t.index('<g transform="translate(310,36)">')
    j = t.index('</g>', i)
    return t[i:j]

def boxes(g):
    out = []
    for m in re.finditer(r'<rect class="([^"]*)" x="(-?[\d.]+)" y="(-?[\d.]+)" width="([\d.]+)" height="([\d.]+)"', g):
        cls, x, y, w, h = m.group(1), *map(float, m.groups()[1:])
        if 'd-key' in cls: continue
        out.append((cls, x, y, x + w, y + h))
    return out

BUS = set()          # indices of the bus bars, whose ends are open and named

def polylines(g):
    """Every drawn line, as a list of subpaths, each a list of points."""
    out = []
    BUS.clear()
    for m in re.finditer(r'<(path|line) class="(d-line|d-bus)[^"]*"([^>]*)/>', g):
        kind, attrs = m.group(1), m.group(3)
        if m.group(2) == 'd-bus': BUS.add(len(out))
        if kind == 'line':
            v = dict(re.findall(r'(x1|y1|x2|y2)="(-?[\d.]+)"', attrs))
            out.append([[(float(v['x1']), float(v['y1'])), (float(v['x2']), float(v['y2']))]])
        else:
            d = re.search(r'd="([^"]+)"', attrs).group(1)
            subs, cur = [], []
            for c in re.finditer(r'([MLml])\s*(-?[\d.]+),(-?[\d.]+)', d):
                p = (float(c.group(2)), float(c.group(3)))
                if c.group(1) in 'Mm':
                    if len(cur) > 1: subs.append(cur)
                    cur = [p]
                else:
                    cur.append(p)
            if len(cur) > 1: subs.append(cur)
            out.append(subs)
    return out

def on_box(p, bs):
    x, y = p
    for cls, x0, y0, x1, y1 in bs:
        if x0 - EPS <= x <= x1 + EPS and (abs(y - y0) < EPS or abs(y - y1) < EPS): return cls
        if y0 - EPS <= y <= y1 + EPS and (abs(x - x0) < EPS or abs(x - x1) < EPS): return cls
    return None

def on_segment(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    if abs(ax - bx) < EPS:                       # vertical
        return abs(px - ax) < EPS and min(ay, by) - EPS <= py <= max(ay, by) + EPS
    if abs(ay - by) < EPS:                       # horizontal
        return abs(py - ay) < EPS and min(ax, bx) - EPS <= px <= max(ax, bx) + EPS
    # a diagonal: parametric
    dx, dy = bx - ax, by - ay
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    if not -0.01 <= t <= 1.01: return False
    return abs(ax + t * dx - px) < EPS and abs(ay + t * dy - py) < EPS

def main():
  bad = 0
  for f in ('arty-z7-20', 'cora-z7-07s'):
      t = open(os.path.join(D, f + '.html')).read()
      g = arch(t)
      bs = boxes(g)
      pls = polylines(g)
      ends = 0
      for i, subs in enumerate(pls):
          if i in BUS: continue          # a bus bar's ends are open, and named
          for sub in subs:
              for p in (sub[0], sub[-1]):
                  ends += 1
                  if on_box(p, bs): continue
                  ok = False
                  for j, other in enumerate(pls):
                      for osub in other:
                          if j == i and osub is sub: continue
                          for a, b in zip(osub, osub[1:]):
                              if on_segment(p, a, b): ok = True; break
                          if ok: break
                      if ok: break
                  if not ok:
                      print('%s: end %s in mid-air' % (f, p)); bad += 1
      # boxes that overlap without one containing the other
      ov = 0
      for a in range(len(bs)):
          for b in range(a + 1, len(bs)):
              ca, ax0, ay0, ax1, ay1 = bs[a]
              cb, bx0, by0, bx1, by1 = bs[b]
              ix = min(ax1, bx1) - max(ax0, bx0); iy = min(ay1, by1) - max(ay0, by0)
              if ix > EPS and iy > EPS:
                  contains = ((ax0 <= bx0 + EPS and ax1 >= bx1 - EPS and ay0 <= by0 + EPS and ay1 >= by1 - EPS)
                              or (bx0 <= ax0 + EPS and bx1 >= ax1 - EPS and by0 <= ay0 + EPS and by1 >= ay1 - EPS))
                  if not contains:
                      print('%s: boxes overlap: %s %s | %s %s' % (f, ca, (ax0,ay0,ax1,ay1), cb, (bx0,by0,bx1,by1)))
                      ov += 1; bad += 1
      print('%-14s %3d boxes, %3d lines, %3d ends checked, %d overlap(s)' % (f, len(bs), len(pls), ends, ov))
  print('geometry:', 'OK' if not bad else '%d problem(s)' % bad)
  sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
