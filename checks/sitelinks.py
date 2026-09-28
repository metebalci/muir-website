#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Every link the four projects make into the site resolves on it.

    python3 checks/sitelinks.py --repos DIR [--root DIR] [--ref REF]

DIR (--repos) holds clones of muir-sim, muir-sys, muir-fpga and ozd, as for
checks/links.py; a clone needs no checkout.  Over every tracked text file of
each at REF (default main):
  - every muir.metebalci.com URL, with or without its scheme, names a file
    in pages/ (a directory naming its index.html, a path without .html its
    .html page, as GitHub Pages serves them), and its #anchor an id on that
    page;
  - no URL names the projects' retired sites (muir-sim, muir-sys, muir-fpga,
    ozd or coldboot .metebalci.com), which no longer resolve.
It prints each broken link as repository:path:line and exits 1 if there is
any, or if a clone is missing."""
import argparse, os, re, subprocess, sys
from urllib.parse import unquote, urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import links  # noqa: E402

REPOS = ('muir-sim', 'muir-sys', 'muir-fpga', 'ozd')
SITE = 'muir'
RETIRED = ('muir-sim', 'muir-sys', 'muir-fpga', 'ozd', 'coldboot')
URL = re.compile(r'(?<![\w.-])(?:https?://)?([a-z0-9-]+)\.metebalci\.com(?![\w-])(?!\.\w)([^\s<>"\'`()\[\]{}|\\,;]*)', re.I)


def site_links(repo, ref):
    """(path, line, url) for every <x>.metebalci.com URL in the repository's
    tracked text files at ref."""
    r = subprocess.run(['git', '-C', repo, 'grep', '-I', '-n', '-i', '-E', r'[a-z0-9-]\.metebalci\.com', ref, '--'],
                       capture_output=True, text=True)
    if r.returncode not in (0, 1):
        raise RuntimeError('git grep in %s: %s' % (repo, r.stderr.strip()))
    for row in r.stdout.splitlines():
        _, path, line, text = row.split(':', 3)
        for m in URL.finditer(text):
            yield path, int(line), m.group(1).lower(), m.group(0), m.group(2).rstrip('.:!?*_')


def resolve(pages, rest):
    """None if the path and #anchor after muir.metebalci.com resolve in
    pages/, else why."""
    u = urlsplit('https://site' + (rest if rest.startswith(('/', '#', '?')) else '/' + rest))
    f = links.resolve(pages, os.path.join(pages, 'index.html'), unquote(u.path) or '/')
    if f is None:
        return 'outside the site'
    if not os.path.isfile(f) and os.path.isfile(f + '.html'):
        f += '.html'
    if not os.path.isfile(f):
        return 'no such page'
    if u.fragment:
        if not f.endswith('.html'):
            return 'an anchor on a page that is not HTML'
        if u.fragment not in links.parse(f).ids:
            return 'no id "%s" on %s' % (u.fragment, os.path.relpath(f, pages))
    return None


def check(root, repos, ref='main'):
    pages = os.path.join(root, 'pages')
    links._PAGES.clear()
    problems = []
    for name in REPOS:
        d = os.path.join(repos, name)
        if not os.path.isdir(d):
            problems.append('%s: no clone under --repos' % name)
            continue
        for path, line, host, url, rest in site_links(d, ref):
            where = '%s:%s:%d: %s' % (name, path, line, url)
            if host in RETIRED:
                problems.append('%s: a retired site' % where)
            elif host == SITE:
                why = resolve(pages, rest)
                if why:
                    problems.append('%s: %s' % (where, why))
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=os.path.dirname(HERE))
    ap.add_argument('--repos', required=True)
    ap.add_argument('--ref', default='main')
    a = ap.parse_args()
    problems = check(a.root, a.repos, a.ref)
    for p in problems:
        print(p)
    print('sitelinks: %d broken' % len(problems))
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
