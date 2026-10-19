#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Every figure that differs from board to board comes from gen/facts.py.

    python3 checks/facts.py [--root DIR]

Builds the whole site into a scratch directory with every figure in
gen/facts.py moved (MUIR_SITE_FACTS_PERTURB=1), so a page built from the
figures carries none of the real ones.  It then
looks in what each page shows, its text and its aria-label, alt, title and
description attributes, for the real figures:

  - QUUX's period on a board, "19 ns", "19 nanoseconds";
  - QUUX's cache on a board, "64K" or "65,536", where "cache" is near it;
  - QUUX's main memory on a board, and the most a released card offers,
    "32MW", "32 megawords", where a board's name is near it;
  - a board's display, "1920 by 1080", "1920x1080", but for the video
    controller's limit ("up to", "at most", "above" it);
  - each fit's logic, "15,187", its block memory label, "207 KB of 630 KB",
    and its worst setup slack, "0.275";
  - Linux's share of a board's memory, "493,976".

A real figure found there was written by hand, and it is reported with its
page and the words around it.  It exits 1 on any."""
import argparse, html, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PERTURB = 'MUIR_SITE_FACTS_PERTURB'
NEAR = 100          # how far, in characters, a figure's context may be
BOARD_NAMES = r'Arty|Kria|KR260|DE25'


def load_facts(root):
    """gen/facts.py with its real figures."""
    import importlib.util
    env = os.environ.pop(PERTURB, None)
    try:
        spec = importlib.util.spec_from_file_location('site_facts', os.path.join(root, 'gen', 'facts.py'))
        F = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(F)
    finally:
        if env is not None:
            os.environ[PERTURB] = env
    assert not F.PERTURB
    return F


def number(text):
    """A number as a pattern that no longer digit or decimal surrounds."""
    return r'(?<![\d.,])%s(?![\d]|[.,]\d)' % re.escape(text)


def figures(F):
    """(what, pattern, the context that must be near it or None)."""
    out = []
    for b in F.QUUX:
        name = F.NAME[b]
        out.append(('%s: QUUX period' % name, number(F.period(b)) + r'\s*(?:ns|nanoseconds)\b', None))
        for form in sorted({F.cache_k(b), F.cache_words(b)}):
            # a TLB of 4,096 entries is not a cache of 4,096 words
            out.append(('%s: QUUX cache' % name, number(form) + r'(?![\s|]*entries)', r'(?i)cache'))
    for mw in sorted({F.QUUX[b]['memory'] for b in F.QUUX} | set(F.CARD_MEMORY_MOST.values())):
        out.append(('QUUX main memory, %dMW' % mw, number(str(mw)) + r'\s*(?:MW|megawords|M words)\b', BOARD_NAMES))
    for b, (_, w, h) in F.DISPLAY.items():
        # "up to", "at most" and "above" give the video controller's limit,
        # which is the design's and not a board's
        out.append(('%s: display' % F.NAME[b], r'(?<!up to )(?<!at most )(?<!above )(?<![\d.,])%d\s*(?:by|x|\u00d7)\s*%d(?!\d)(?![\s|]*at most)' % (w, h), None))
    for (b, machine), f in F.FITS.items():
        what = '%s: %s fit' % (F.NAME[b], machine.upper())
        out.append((what + ', logic', number(F.num(f.logic)), None))
        out.append((what + ', block memory', re.escape(F.memory_label(f).split(' ', 1)[1]), None))
        out.append((what + ', setup slack', number(F.setup(f).lstrip('+')), None))
    for b, kb in F.LINUX_CADR_KB.items():
        out.append(('%s: Linux beside the CADR' % F.NAME[b], number(F.num(kb)), None))
    for b, (v, unit) in F.LINUX_QUUX.items():
        out.append(('%s: Linux beside QUUX' % F.NAME[b], number(F.num(v)) + r'\s*' + unit, None))
    return out


def shown(page):
    """What a page shows: its text, and the attributes a reader is given."""
    t = re.sub(r'<!--.*?-->', ' ', page, flags=re.S)
    t = re.sub(r'<(script|style)\b.*?</\1>', ' ', t, flags=re.S)
    attrs = re.findall(r'\s(?:aria-label|alt|title|content)="([^"]*)"', t)
    t = re.sub(r'<[^>]*>', ' | ', t)
    text = ' | '.join(attrs) + ' | ' + t
    text = html.unescape(text).replace(' ', ' ')
    return re.sub(r'\s+', ' ', text)


def check(root):
    F = load_facts(root)
    problems = []
    with tempfile.TemporaryDirectory() as out:
        env = dict(os.environ, **{PERTURB: '1'})
        r = subprocess.run([sys.executable, '-B', os.path.join(root, 'gen', 'build.py'), out],
                           capture_output=True, text=True, env=env)
        if r.returncode != 0:
            return ['gen/build.py failed with the figures moved:\n' + r.stderr]
        pats = [(w, re.compile(p), re.compile(c) if c else None) for w, p, c in figures(F)]
        for rel in sorted(r.stdout.split()):
            text = shown(open(os.path.join(out, rel), encoding='utf-8').read())
            for what, pat, near in pats:
                for m in pat.finditer(text):
                    around = text[max(0, m.start() - NEAR):m.end() + NEAR]
                    if near and not near.search(around):
                        continue
                    problems.append('pages/%s: %s written by hand: ...%s...'
                                    % (rel, what, text[max(0, m.start() - 60):m.end() + 40].strip()))
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=os.path.dirname(HERE))
    a = ap.parse_args()
    problems = check(a.root)
    for p in problems:
        print(p)
    print('facts: %d figure%s written by hand' % (len(problems), '' if len(problems) == 1 else 's'))
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
