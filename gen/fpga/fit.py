# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fits the labels of muir-fpga's drawings to their boxes in IBM Plex Mono.

The drawings were placed by measurement in a proportional face; their labels
are now set in Plex Mono, whose advance is 600 units to the em at every weight
(read from the served ibm-plex-mono-400.woff2 and -500.woff2 in Chromium: a
space, `M`, `i`, `W`, `x`, a digit, `.` and `%` each measured 600), so a label
of n letters at s units is n * 0.6 * s units wide, whatever it says.

A group is the consecutive `<text>` lines of one drawing that share a class,
an x, an anchor and, where there is one, a box, at most 19 units apart: one
paragraph the drawing broke by hand.  A label turned on its side, or sized by a style of its own, is left as it is.  Where a line of a group is wider than
the room it has, the group is set again, its words filled greedily line by
line from the same first baseline at the same line step.

  - In a box, the room is the box less MARGIN each side, and it is done only
    where the last line still sits inside the box.  The groups below it in the
    same box move down by the lines it gained.  If any group of a box cannot
    be fitted the whole box is left as it was and listed in UNFITTED, and
    gen.py's LABELS says what to write instead.
  - Outside any box, the room is what is left of the drawing to its edge, and
    the groups below it at the same x and anchor and of the same class move
    down by the lines it gained, for as long as each is within COLUMN_GAP of
    the last, and the column is left as it was if one of another class is
    within reach; the drawing grows by the same at its foot where that is
    needed.
"""
import html as H
import re

ADVANCE = 0.6
SIZE = {'d-t': 13, 'd-s': 11, 'd-m': 13, 'd-n': 11, 'd-x': 9.5}
MARGIN = 2.5          # kept clear between a label and the box's edge, each side
EDGE = 10           # kept clear between a label and the drawing's edge
STEP_MAX = 19       # farthest apart two lines of one paragraph are
COLUMN_GAP = 60     # farthest a group can be below the last and still move with it
TEXT = re.compile(r'^(\s*)<text class="([^"]*)" x="(-?[\d.]+)" y="(-?[\d.]+)"(?: text-anchor="(\w+)")?((?: [\w-]+="[^"]*")*)>([^<]*)</text>\s*$')
RECT = re.compile(r'<rect class="([^"]*)" x="(-?[\d.]+)" y="(-?[\d.]+)" width="([\d.]+)" height="([\d.]+)"')

UNFITTED = []       # (page label, text) of every group left as it was


def size_of(cls, sizes=SIZE):
    for c in cls.split():
        if c in sizes:
            return sizes[c]
    return 11


def _num(v):
    return '%g' % v


def _line(it, y, words):
    anc = ' text-anchor="%s"' % it['anc'] if it['anc'] != 'start' else ''
    return '%s<text class="%s" x="%s" y="%s"%s%s>%s</text>' % (it['ind'], it['cls'], _num(it['x']), _num(y), anc, it['rest'], words)


def _wrap(words, cap):
    out, cur = [], ''
    for w in words.split(' '):
        cand = (cur + ' ' + w).strip()
        if len(H.unescape(cand)) <= cap or not cur:
            cur = cand
        else:
            out.append(cur)
            cur = w
    out.append(cur)
    return out


PATH = re.compile(r'<path\b[^>]*?\sd="([^"]*)"')
TOKEN = re.compile(r'([MLHV])|(-?\d+(?:\.\d+)?)')


def _vertices(d):
    """[(x, y, index of the token holding y, index of the token holding x)] of an
    absolute M, L, H, V path, or None where it uses anything else."""
    if re.search(r'[A-Za-z]', re.sub(r'[MLHV]', '', d)):
        return None
    toks = TOKEN.findall(d)
    out, x, y, i, cmd = [], 0.0, 0.0, 0, None
    seq = []
    for c, n in toks:
        if c:
            cmd = c
        else:
            seq.append((cmd, float(n)))
    k = 0
    while k < len(seq):
        cmd, v = seq[k]
        if cmd in 'ML':
            x, y = v, seq[k + 1][1]
            k += 2
        elif cmd == 'H':
            x = v
            k += 1
        else:
            y = v
            k += 1
        out.append((x, y, cmd, k))
    return out


def _move_vertices(d, moves):
    """`d` with every vertex (x, y) in `moves` (a dict to the new y) moved."""
    toks = list(TOKEN.finditer(d))
    seq, cmd = [], None
    for m in toks:
        if m.group(1):
            cmd = m.group(1)
        else:
            seq.append([cmd, m, float(m.group(2))])
    verts, x, y, k = [], 0.0, 0.0, 0
    while k < len(seq):
        cmd, m, v = seq[k]
        if cmd in 'ML':
            x, y = v, seq[k + 1][2]
            verts.append((x, y, seq[k + 1][1]))
            k += 2
        elif cmd == 'H':
            x = v
            k += 1
        else:
            y = v
            verts.append((x, y, m))
            k += 1
    edits = []
    for x, y, m in verts:
        if (x, y) in moves:
            edits.append((m.start(2), m.end(2), _num(moves[(x, y)])))
    for s, e, new in sorted(edits, reverse=True):
        d = d[:s] + new + d[e:]
    return d


def fit_labels(text, where='', sizes=SIZE):
    lines = text.split('\n')
    spans, cur = [], None
    for i, l in enumerate(lines):
        if '<svg' in l and cur is None:
            cur = i
        if '</svg>' in l and cur is not None:
            spans.append((cur, i))
            cur = None
    edits, grow = {}, {}
    for a, b in spans:
        vb = re.search(r'viewBox="([-\d. ]+)"', lines[a])
        vx, vy, vw, vh = map(float, vb.group(1).split()) if vb else (0, 0, 1e9, 1e9)
        rects = []
        for i in range(a, b + 1):
            m = RECT.search(lines[i])
            if m and 'd-key' not in m.group(1) and 'd-plate' not in m.group(1):
                x, y, w, h = map(float, m.groups()[1:])
                if w < vw * 0.98:
                    rects.append((x, y, x + w, y + h))

        rect_lines, path_lines = [], []
        for i in range(a, b + 1):
            m = RECT.search(lines[i])
            if m:
                x, y, w, h = map(float, m.groups()[1:])
                rect_lines.append((i, x, y, w, h))
            m = PATH.search(lines[i])
            if m:
                path_lines.append((i, m.group(1)))

        def try_grow(bx, dy, texts_of_box):
            """The edits that lower the bottom edge of box `bx` by `dy`, or None
            where anything but a line that ends on that edge is in the way."""
            x0, y0, x1, y1 = bx
            sx0, sx1, sy0, sy1 = x0 - 2, x1 + 2, y1 + 2, y1 + dy + 2
            for i, x, y, w, h in rect_lines:
                if (x, y, x + w, y + h) == bx:
                    continue
                if x <= sx0 and x + w >= sx1 and y <= sy0 and y + h >= sy1:
                    continue        # an outline that holds the strip
                if x < sx1 and x + w > sx0 and y < sy1 and y + h > sy0:
                    return None
            for it in items:
                if it['i'] in texts_of_box:
                    continue
                wd = len(H.unescape(it['txt'])) * ADVANCE * it['size']
                left = it['x'] - (wd / 2 if it['anc'] == 'middle' else wd if it['anc'] == 'end' else 0)
                if left < sx1 and left + wd > sx0 and it['y'] - 0.75 * it['size'] < sy1 and it['y'] + 0.25 * it['size'] > y1 - 2:
                    return None
            moves = {}
            for i, d in path_lines:
                vs = _vertices(d)
                if vs is None:
                    nums = [float(n) for n in re.findall(r'-?\d+(?:\.\d+)?', d)]
                    pts = list(zip(nums[0::2], nums[1::2]))
                    if any(sx0 <= px <= sx1 and sy0 <= py <= sy1 for px, py in pts):
                        return None
                    continue
                for (xa, ya, _, _), (xb, yb, _, _) in zip(vs, vs[1:]):
                    if xa != xb and any(py == y1 and x0 <= px <= x1 for px, py in ((xa, ya), (xb, yb))):
                        return None     # a cross drawn corner to corner
                    lo_x, hi_x, lo_y, hi_y = min(xa, xb), max(xa, xb), min(ya, yb), max(ya, yb)
                    if hi_x < sx0 or lo_x > sx1 or hi_y < sy0 or lo_y > sy1:
                        continue
                    ends = [(px, py) for px, py in ((xa, ya), (xb, yb)) if py == y1 and x0 <= px <= x1]
                    if xa == xb and ends and lo_y == y1:
                        moves.setdefault(i, {}).update({e: y1 + dy for e in ends})
                        continue
                    return None
            new = {}
            for i, x, y, w, h in rect_lines:
                if (x, y, x + w, y + h) == bx:
                    new[i] = re.sub(r'height="[\d.]+"', 'height="%s"' % _num(h + dy), lines[i], count=1)
            for i, mv in moves.items():
                new[i] = re.sub(r'(\sd=")([^"]*)"', lambda m: m.group(1) + _move_vertices(m.group(2), mv) + '"', lines[i], count=1)
            return new

        def box(x, y):
            best = None
            for r in rects:
                if r[0] <= x <= r[2] and r[1] <= y - 3 <= r[3]:
                    if best is None or (r[2] - r[0]) * (r[3] - r[1]) < (best[2] - best[0]) * (best[3] - best[1]):
                        best = r
            return best
        items = []
        for i in range(a, b + 1):
            m = TEXT.match(lines[i])
            if m and 'transform=' not in m.group(6) and 'style=' not in m.group(6):
                ind, cls, x, y, anc, rest, txt = m.groups()
                items.append(dict(i=i, ind=ind, cls=cls, x=float(x), y=float(y), anc=anc or 'start', rest=rest, txt=txt, size=size_of(cls, sizes)))
        groups, g = [], []
        for it in items:
            if g:
                p = g[-1]
                if (it['i'] == p['i'] + 1 and it['cls'] == p['cls'] and it['x'] == p['x'] and it['anc'] == p['anc'] and it['rest'] == p['rest']
                        and 0 < it['y'] - p['y'] <= STEP_MAX and box(it['x'], it['y']) == box(p['x'], p['y'])):
                    g.append(it)
                    continue
                groups.append(g)
                g = []
            g.append(it)
        if g:
            groups.append(g)
        for g in groups:
            g[0]['box'] = box(g[0]['x'], g[0]['y'])
        boxed, column = {}, {}
        for g in groups:
            e = g[0]
            if e['box'] is not None:
                boxed.setdefault(e['box'], []).append(g)
            else:
                column.setdefault((e['x'], e['anc']), []).append(g)

        def room(e, bx):
            if bx is not None:
                if e['anc'] == 'middle':
                    return (bx[2] - bx[0]) - 2 * MARGIN
                if e['anc'] == 'end':
                    return e['x'] - bx[0] - MARGIN
                return bx[2] - e['x'] - MARGIN
            if e['anc'] == 'middle':
                return 2 * min(e['x'] - vx, vx + vw - e['x']) - 2 * EDGE
            if e['anc'] == 'end':
                return e['x'] - vx - EDGE
            return vx + vw - e['x'] - EDGE

        def flow(gs, bx, bottom):
            """The edits that set the groups of one box, or of one column, in
            order, or None when one cannot be set."""
            shift, out, failed, prev, moved_cls = 0.0, {}, [], None, None
            for g in gs:
                e = g[0]
                if bx is None and prev is not None and shift and e['y'] - prev > COLUMN_GAP:
                    shift = 0.0
                prev = g[-1]['y']
                cap = int(room(e, bx) // (ADVANCE * e['size']) + 1e-9)
                texts = [H.unescape(x['txt']) for x in g]
                over = any(len(t) > cap for t in texts)
                step = (g[1]['y'] - g[0]['y']) if len(g) > 1 else 14
                if not over:
                    if shift and bx is None and e['cls'] != moved_cls:
                        # a label of another kind below is placed against the
                        # drawing, not against the words above it
                        failed.append(' | '.join(texts))
                        continue
                    if shift:
                        if bx is not None and g[-1]['y'] + shift > bottom - 4:
                            failed.append(' | '.join(texts))
                            continue
                        for x in g:
                            out[x['i']] = [_line(x, x['y'] + shift, x['txt'])]
                    continue
                wl = _wrap(' '.join(x['txt'] for x in g), cap)
                y0 = e['y'] + shift
                ylast = y0 + step * (len(wl) - 1)
                if (bx is not None and ylast > bottom - 4) or any(len(H.unescape(w)) > cap for w in wl):
                    failed.append(' | '.join(texts))
                    continue
                if bx is None and len(wl) > len(g):
                    wd = max(len(H.unescape(w)) for w in wl) * ADVANCE * e['size']
                    left = e['x'] - (wd / 2 if e['anc'] == 'middle' else wd if e['anc'] == 'end' else 0)
                    ylo, yhi = g[-1]['y'] + shift + 0.25 * e['size'], ylast + 0.25 * e['size']
                    if any(rx < left + wd and rx + rw > left and ry < yhi and ry + rh > ylo
                           and not (rx <= left and rx + rw >= left + wd and ry <= ylo and ry + rh >= yhi)
                           for _, rx, ry, rw, rh in rect_lines):
                        failed.append(' | '.join(texts))    # the lines it gains would run into a box
                        continue
                out[g[0]['i']] = [_line(e, y0 + step * j, w) for j, w in enumerate(wl)]
                moved_cls = e['cls']
                for x in g[1:]:
                    out[x['i']] = []
                shift += (len(wl) - len(g)) * step
            return out, failed, shift

        for bx, gs in boxed.items():
            out, failed, _ = flow(gs, bx, bx[3])
            grown = {}
            if failed:
                out2, failed2, _ = flow(gs, bx, 1e9)
                if not failed2:
                    ys = [float(re.search(r' y="(-?[\d.]+)"', s).group(1)) for ss in out2.values() for s in ss]
                    ys += [x['y'] for g in gs for x in g]
                    need = int(max(ys) + 4 - bx[3] + 0.999)
                    own = set(x['i'] for g in gs for x in g)
                    grown = try_grow(bx, need, own) if need > 0 else None
                    if grown is not None:
                        out, failed = out2, []
            if failed:
                UNFITTED.extend((where, f) for f in failed)
            else:
                edits.update(out)
                edits.update(dict((i, [s]) for i, s in grown.items()))
        for key, gs in column.items():
            out, failed, shift = flow(sorted(gs, key=lambda g: g[0]['y']), None, 1e9)
            if failed:
                UNFITTED.extend((where, f) for f in failed)
                continue
            edits.update(out)
            if out:
                lowest = 0.0
                for i, l in out.items():
                    for s in l:
                        m = re.search(r' y="(-?[\d.]+)"', s)
                        lowest = max(lowest, float(m.group(1)))
                if lowest > vy + vh - 6:
                    grow[a] = max(grow.get(a, 0.0), lowest + 12 - (vy + vh))
    out = []
    for i, l in enumerate(lines):
        for s in (edits[i] if i in edits else [l]):
            if i in grow:
                s = re.sub(r'viewBox="([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)"',
                           lambda m: 'viewBox="%s %s %s %s"' % (m.group(1), m.group(2), m.group(3), _num(float(m.group(4)) + grow[i])), s, count=1)
            out.append(s)
    return '\n'.join(out)
