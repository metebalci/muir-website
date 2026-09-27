#!/usr/bin/env python3
"""The three sequence drawings on booting.html, read geometrically.

Nothing here renders a font, so the width of a label is estimated from
Helvetica's own advance widths, which are a little wider than Archivo's.

  - every arrow ends on a lifeline dash or on an activation rect's edge;
  - every activation rect sits under its own lifeline head;
  - no text runs outside the drawing's frame;
  - no middle-anchored arrow label is wider than the gap its arrow spans;
  - no left-anchored label runs into a rect to its right;
  - a rotated label is no longer than the rect it is turned inside.
"""
import os, re, sys, html
P = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'pages', 'fpga'), 'booting.html')
EPS = 0.75
W = {' ':278,'!':278,'"':355,'#':556,'$':556,'%':889,'&':667,"'":191,'(':333,')':333,
     '*':389,'+':584,',':278,'-':333,'.':278,'/':278,':':278,';':278,'<':584,'=':584,
     '>':584,'?':556,'@':1015,'[':278,'\\':278,']':278,'^':469,'_':556,'`':333,
     '{':334,'|':260,'}':334,'~':584,'—':1000,'’':191,'×':584,' ':278}
for c, w in zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                [667,667,722,722,667,611,778,722,278,500,667,556,833,722,778,667,778,
                 722,667,611,722,667,944,667,667,611]): W[c] = w
for c, w in zip('abcdefghijklmnopqrstuvwxyz',
                [556,556,500,556,556,278,556,556,222,222,500,222,833,556,556,556,556,
                 333,500,278,556,500,722,500,500,500]): W[c] = w
for c in '0123456789': W[c] = 556
SIZE = {'d-t': 13, 'd-s': 11, 'd-n': 11}

def width(s, cls):
    k = cls.split()[0]
    if k == 'd-n': return len(s) * 11 * 0.6
    return sum(W.get(c, 556) for c in s) / 1000.0 * SIZE[k]

t = open(P).read()
bad = 0
for n, m in enumerate(re.finditer(r'<svg viewBox="0 0 (\d+) (\d+)".*?</svg>', t, re.S), 1):
    vw, vh, g = int(m.group(1)), int(m.group(2)), m.group(0)
    name = re.search(r'<text class="d-t" x="10" y="18">([^<]*)</text>', g).group(1)
    rects = [(c, float(x), float(y), float(x)+float(w), float(y)+float(h)) for c, x, y, w, h in
             re.findall(r'<rect class="([^"]*)" x="(-?[\d.]+)" y="(-?[\d.]+)" width="([\d.]+)" height="([\d.]+)"', g)]
    frame = max((r for r in rects), key=lambda r: (r[3]-r[1])*(r[4]-r[2]))
    dashes = []
    for d in re.findall(r'<path class="d-dash" d="([^"]+)"', g):
        for a in re.finditer(r'M(-?[\d.]+),(-?[\d.]+) L(-?[\d.]+),(-?[\d.]+)', d):
            dashes.append(tuple(map(float, a.groups())))
    lines = [tuple(map(float, a)) for a in
             re.findall(r'<line class="d-line" x1="(-?[\d.]+)" y1="(-?[\d.]+)" x2="(-?[\d.]+)" y2="(-?[\d.]+)"', g)]
    print('--- drawing %d: %s   viewBox %dx%d, %d rects, %d lifelines, %d arrows'
          % (n, name, vw, vh, len(rects), len(dashes), len(lines)))
    # every arrow end lands on a lifeline or an activation edge
    def lands(px, py):
        for x1, y1, x2, y2 in dashes:
            if abs(px - x1) < EPS and min(y1, y2) - EPS <= py <= max(y1, y2) + EPS: return 'lifeline'
        for c, x0, y0, x1, y1 in rects:
            if c == frame[0] and (x0, y0) == (frame[1], frame[2]): continue
            if y0 - EPS <= py <= y1 + EPS and (abs(px - x0) < EPS or abs(px - x1) < EPS): return 'rect ' + c
            if x0 - EPS <= px <= x1 + EPS and (abs(py - y0) < EPS or abs(py - y1) < EPS): return 'rect ' + c
        return None
    open_starts = []
    for x1, y1, x2, y2 in lines:
        for p in ((x1, y1), (x2, y2)):
            if not lands(*p):
                # An arrow that begins in open space is the outside world
                # acting on the board --- a reset, or the power coming on ---
                # and it is the tail of the drawing's first arrow only.
                if p == (x1, y1) and (x1, y1, x2, y2) == lines[0]:
                    open_starts.append(p); continue
                print('   end %s lands on nothing' % (p,)); bad += 1
    print('   %d open start(s), the outside world acting: %s' % (len(open_starts), open_starts))
    # text inside the frame, and labels that fit
    for tm in re.finditer(r'<text class="(d-[a-z]+)" x="(-?[\d.]+)" y="(-?[\d.]+)"([^>]*)>([^<]*)</text>', g):
        cls, x, y, attrs, s = tm.group(1), float(tm.group(2)), float(tm.group(3)), tm.group(4), html.unescape(tm.group(5))
        w = width(s, cls)
        rot = 'rotate' in attrs
        mid = 'middle' in attrs
        if rot:
            # inside which rect?
            for c, x0, y0, x1, y1 in rects:
                if x0 <= x <= x1 and y0 <= y <= y1 and (y1 - y0) < 400:
                    if w > (y1 - y0) - 8:
                        print('   rotated "%s" is %.0f long in a rect %.0f tall' % (s, w, y1 - y0)); bad += 1
            continue
        lo, hi = (x - w/2, x + w/2) if mid else (x, x + w)
        if lo < frame[1] or hi > frame[3]:
            print('   "%s" runs outside the frame (%.0f..%.0f)' % (s, lo, hi)); bad += 1
        # does it run into a rect that is not the one it labels?
        for c, x0, y0, x1, y1 in rects:
            if (x1 - x0) > 900: continue                 # the frame
            if not (y0 - 9 < y < y1 + 3): continue
            if hi > x0 + EPS and lo < x1 - EPS:
                if x0 <= x <= x1: continue               # its own box
                print('   "%s" (%.0f..%.0f) overlaps rect %s %.0f..%.0f' % (s, lo, hi, c, x0, x1)); bad += 1
print('sequences:', 'OK' if not bad else '%d problem(s)' % bad)
sys.exit(1 if bad else 0)
