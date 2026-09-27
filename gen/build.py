#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Builds every page of the site into pages/, or into the directory given.

The pages written by hand are in src/: each is what goes inside <main>,
after a comment of `key: value` lines that give its title, its description
and what else it loads.  muir-fpga's pages are written by gen/fpga/gen.py.
Both are wrapped in gen/chrome.py's head, header and footer.  The two
full-size image pages, simulator/lashup.html and simulator/system-100.html,
are not built: they are pages/ files of their own.

    python3 gen/build.py            # into pages/
    python3 gen/build.py <dir>      # somewhere else, to compare with pages/
"""
import os, re, sys

# No bytecode: a cached copy of a generator edited and put back within one
# second would be taken for the source.
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import chrome  # noqa: E402

SRC = os.path.join(ROOT, 'src')


def meta_and_main(text):
    m = re.match(r'<!--\n(.*?)\n-->\n', text, re.S)
    assert m, 'a src page starts with its comment of key: value lines'
    meta = {}
    for line in m.group(1).splitlines():
        k, v = line.split(':', 1)
        meta[k.strip()] = v.strip()
    return meta, text[m.end():]


def build_src(out):
    written = []
    for dirpath, _, files in os.walk(SRC):
        for f in sorted(files):
            if not f.endswith('.html'):
                continue
            rel = os.path.relpath(os.path.join(dirpath, f), SRC)
            meta, main = meta_and_main(open(os.path.join(dirpath, f), encoding='utf-8').read())
            section = rel.split('/')[0] if '/' in rel else None
            css = tuple(c for c in meta.get('css', '').split() if c)
            html = chrome.page(rel, meta['title'], meta['description'], main, section=section,
                               css=css, script=meta.get('script') == 'yes',
                               body_class=meta.get('body') or None)
            dest = os.path.join(out, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, 'w', encoding='utf-8').write(html)
            written.append(rel)
    return written


def build(out):
    written = build_src(out)
    sys.path.insert(0, os.path.join(HERE, 'fpga'))
    import gen as fpga  # noqa: E402
    written += ['fpga/' + f for f in fpga.main(os.path.join(out, 'fpga'))]
    return sorted(written)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'pages')
    for rel in build(out):
        print(rel)
