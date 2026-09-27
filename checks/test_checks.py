#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Each check is shown able to fail before it is trusted.

    python3 checks/test_checks.py [--repos DIR] [--ref REF]

Copies the repository into a scratch directory, runs every check on the
copy as it is (each must pass), then plants one fault at a time, runs the
check that should catch it, and requires it to fail; each fault is taken
back out before the next.  With --repos the GitHub part of the link check
is tested too.  It prints one line a fault and exits 1 if a check passed a
fault or failed the clean copy."""
import argparse, os, shutil, socket, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import generated, links, public  # noqa: E402

COPY = ('pages', 'src', 'gen', 'checks', '.github', 'README.md')


def edit(path, old, new):
    s = open(path, encoding='utf-8').read()
    assert s.count(old) >= 1, (path, old)
    open(path, 'w', encoding='utf-8').write(s.replace(old, new, 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repos')
    ap.add_argument('--ref', default='main')
    a = ap.parse_args()
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        root = os.path.join(tmp, 'site')
        os.makedirs(root)
        for c in COPY:
            src = os.path.join(ROOT, c)
            if os.path.isdir(src):
                shutil.copytree(src, os.path.join(root, c), ignore=shutil.ignore_patterns('__pycache__'))
            elif os.path.exists(src):
                shutil.copy(src, os.path.join(root, c))
        P = lambda *p: os.path.join(root, *p)
        runs = {
            'links': lambda: links.check(root, a.repos, a.ref),
            'public': lambda: public.check(root),
            'generated': lambda: generated.check(root),
        }
        for name, run in runs.items():
            got = run()
            ok = not got
            failed += not ok
            print('%-9s the clean copy passes: %s%s' % (name, 'yes' if ok else 'NO', '' if ok else ' ' + '; '.join(got[:3])))

        faults = [
            ('links', 'a link to a page that does not exist',
             P('pages', 'index.html'), 'href="simulator/quux.html"', 'href="simulator/quux-gone.html"'),
            ('links', '#no-such on a page that exists',
             P('pages', 'index.html'), 'href="simulator/#install"', 'href="simulator/#no-such"'),
            ('links', 'an image that is not there',
             P('pages', 'simulator', 'index.html'), 'src="lashup-small.gif"', 'src="lashup-tiny.gif"'),
            ('links', 'a font the stylesheet names and pages/ lacks',
             P('pages', 'style.css'), "fonts/ibm-plex-mono-500.woff2", "fonts/ibm-plex-mono-600.woff2"),
            ('public', 'a home directory in a comment of the generator',
             P('gen', 'fpga', 'gen.py'), '# THE MAKERS\' OWN PAGES', '# see /' + 'home/someone/work/site/base\n# THE MAKERS\' OWN PAGES'),
            ('public', 'a private address in a page',
             P('pages', 'ozd', 'index.html'), '--listen 192.0.2.10', '--listen 192.' + '168.1.20'),
            ('public', 'an e-mail address in the README',
             P('README.md'), '# muir-website', '# muir-website\n\nWrite to someone' + '@' + 'example.org.'),
            ('public', 'this machine\'s name in a page',
             P('pages', 'index.html'), '<main id="main">', '<main id="main"><!-- built on %s -->' % socket.gethostname().split('.')[0]),
            ('generated', 'a fit figure changed in the generator and not built',
             P('gen', 'fpga', 'gen.py'), '<td class="num">15,054 of 53,200<span', '<td class="num">15,055 of 53,200<span'),
            ('generated', 'a page edited by hand',
             P('pages', 'system', 'index.html'), '<h2>What it is</h2>', '<h2>What it was</h2>'),
            ('generated', 'a page nothing builds',
             P('pages', 'fpga', 'index.html'), None, 'full-page.html'),
        ]
        if a.repos:
            faults += [
                ('links', 'a GitHub path not in the repository',
                 P('pages', 'index.html'), 'muir-sim/blob/main/docs/quux.md"', 'muir-sim/blob/main/docs/quux-gone.md"'),
                ('links', 'a Markdown heading that is not there',
                 P('pages', 'index.html'), 'muir-sim/blob/main/docs/sources.md"', 'muir-sim/blob/main/docs/sources.md#no-such-heading"'),
            ]
        for name, what, path, old, new in faults:
            if old is None:
                # A stray page beside path, as muir-fpga's ignored draft would be.
                extra = os.path.join(os.path.dirname(path), new)
                shutil.copy(path, extra)
                got = runs[name]()
                os.remove(extra)
            else:
                keep = open(path, encoding='utf-8').read()
                edit(path, old, new)
                got = runs[name]()
                open(path, 'w', encoding='utf-8').write(keep)
            ok = bool(got)
            failed += not ok
            print('%-9s fails on %s: %s%s' % (name, what, 'yes' if ok else 'NO', (' (%s)' % ' / '.join(got[0].splitlines()[-2:])) if got else ''))
    print('test_checks: %s' % ('every check passes the clean copy and fails each fault' if not failed else '%d wrong' % failed))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
