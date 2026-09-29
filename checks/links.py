#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Every internal link of the site resolves.

    python3 checks/links.py [--root DIR] [--repos DIR] [--ref REF]

Over every page in DIR/pages (DIR is the repository, by default the one
this file is in):
  - every href and src that is not another site's names a file that exists
    in pages/, a directory naming its index.html;
  - every #anchor names an id on the page it points at;
  - every url() in a stylesheet names a file that exists.
With --repos, a directory holding clones of muir-sim, muir-sys, muir-fpga and
ozd, also every github.com/metebalci/<repo>/(blob|tree)/<ref>/<path> link:
<ref> names a branch or a tag of that clone, main standing for REF (default
main), any other branch taken as the clone's own or else origin's; the path
exists at that ref, and an #anchor on a Markdown file names one of its
headings, slugged as GitHub slugs them.  A tree/<ref> link with no path
names a branch or tag the clone has, and so does every releases/tag/<tag>
link.

It prints each broken link and exits 1 if there is any."""
import argparse, os, re, subprocess, sys, unicodedata
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

REPOS = ('muir-sim', 'muir-sys', 'muir-fpga', 'ozd', 'muir-website')


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.refs = set(), []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.add(a['id'])
        if tag == 'a' and 'name' in a:
            self.ids.add(a['name'])
        for k in ('href', 'src', 'xlink:href'):
            if k in a and a[k] is not None:
                self.refs.append((tag, a[k], self.getpos()[0]))

    handle_startendtag = handle_starttag


_PAGES = {}


def parse(path):
    if path not in _PAGES:
        p = Page()
        p.feed(open(path, encoding='utf-8').read())
        _PAGES[path] = p
    return _PAGES[path]


def resolve(pages, page_path, target):
    """The file a site-internal link names, or None if it leaves pages/."""
    if target.startswith('/'):
        f = os.path.join(pages, target.lstrip('/'))
    else:
        f = os.path.join(os.path.dirname(page_path), target)
    f = os.path.normpath(f)
    if not (f + os.sep).startswith(os.path.normpath(pages) + os.sep):
        return None
    if os.path.isdir(f):
        f = os.path.join(f, 'index.html')
    return f


def github_slugs(markdown):
    """The anchors GitHub gives a Markdown file's headings: the heading's
    text as rendered, lower-cased, with everything but letters, marks,
    numbers, connector punctuation, spaces and hyphens taken out and the
    spaces made hyphens; a repeated slug takes -1, -2, ..."""
    seen, out = {}, set()
    in_fence = False
    for line in markdown.splitlines():
        if line.lstrip().startswith('```'):
            in_fence = not in_fence
            continue
        m = None if in_fence else re.match(r'^(#{1,6})\s+(.*?)\s*#*\s*$', line)
        if not m:
            continue
        text = m.group(2)
        text = re.sub(r'!?\[([^\]]*)\]\([^)]*\)', r'\1', text)   # links, as their text
        text = re.sub(r'<[^>]+>', '', text)                        # inline HTML
        text = text.replace('`', '')
        text = re.sub(r'(\*\*|__|\*|(?<![\w])_(?=\w)|(?<=\w)_(?![\w]))', '', text)
        slug = ''.join(c for c in text.lower()
                       if c in ' -' or unicodedata.category(c)[0] in 'LMN' or unicodedata.category(c) == 'Pc')
        slug = slug.replace(' ', '-')
        n = seen.get(slug, 0)
        seen[slug] = n + 1
        out.add(slug if n == 0 else '%s-%d' % (slug, n))
    return out


def git(repo, *args):
    return subprocess.run(['git', '-C', repo] + list(args), capture_output=True, text=True)


def git_ref(d, name, ref):
    """The commit a branch or tag named in a GitHub link is at in clone d, or
    None: main is REF; another branch is the clone's own, or else origin's
    (a clone made with --no-checkout has only origin's); then a tag."""
    for want in ([ref] if name == 'main' else
                 ['refs/heads/' + name, 'refs/remotes/origin/' + name, 'refs/tags/' + name]):
        r = git(d, 'rev-parse', '-q', '--verify', want + '^{commit}')
        if r.returncode == 0:
            return r.stdout.strip()
    return None


def check_github(url, repos, ref, cache={}):
    """None if a github.com/metebalci link resolves in the clones, else why."""
    u = urlsplit(url)
    parts = u.path.strip('/').split('/')
    if len(parts) < 2 or parts[0] != 'metebalci':
        return None
    repo = parts[1]
    d = os.path.join(repos, repo)
    if repo not in REPOS:
        return 'not one of the projects\' repositories'
    if not os.path.isdir(d):
        return None if repo == 'muir-website' else 'no clone of %s under --repos' % repo
    if len(parts) >= 4 and parts[2] in ('blob', 'tree'):
        # A ref may hold slashes; GitHub takes the one the repository has.
        for j in range(4, len(parts) + 1):
            at = git_ref(d, '/'.join(parts[3:j]), ref)
            if at:
                break
        else:
            return 'no branch or tag %s in %s' % (parts[3], repo)
        name = '/'.join(parts[3:j])
        path = unquote('/'.join(parts[j:]))
        if not path:
            return None if parts[2] == 'tree' else 'no file named after blob/%s' % name
        r = git(d, 'cat-file', '-t', '%s:%s' % (at, path))
        want = 'blob' if parts[2] == 'blob' else 'tree'
        if r.returncode != 0 or r.stdout.strip() != want:
            return '%s %s is not in %s at %s' % (want, path, repo, name if name != 'main' else ref)
        if u.fragment and parts[2] == 'blob' and path.endswith('.md'):
            key = (d, at, path)
            if key not in cache:
                cache[key] = github_slugs(git(d, 'show', '%s:%s' % (at, path)).stdout)
            if u.fragment not in cache[key]:
                return 'no heading #%s in %s/%s' % (u.fragment, repo, path)
    elif len(parts) >= 5 and parts[2] == 'releases' and parts[3] == 'tag':
        if git(d, 'rev-parse', '-q', '--verify', 'refs/tags/' + parts[4]).returncode != 0:
            return 'no tag %s in %s' % (parts[4], repo)
    return None


def check(root, repos=None, ref='main'):
    pages = os.path.join(root, 'pages')
    _PAGES.clear()
    problems = []
    htmls, csss = [], []
    for dp, _, fs in os.walk(pages):
        for f in fs:
            (htmls if f.endswith('.html') else csss if f.endswith('.css') else []).append(os.path.join(dp, f))
    for path in sorted(htmls):
        rel = os.path.relpath(path, pages)
        for tag, ref_, line in parse(path).refs:
            where = '%s:%d' % (rel, line)
            u = urlsplit(ref_)
            if u.scheme in ('http', 'https'):
                if repos and u.netloc == 'github.com':
                    why = check_github(ref_, repos, ref)
                    if why:
                        problems.append('%s: %s: %s' % (where, ref_, why))
                continue
            if u.scheme in ('mailto', 'data') or u.netloc:
                continue
            if u.path:
                f = resolve(pages, path, unquote(u.path))
                if f is None or not os.path.isfile(f):
                    problems.append('%s: %s: no such file' % (where, ref_))
                    continue
            else:
                f = path
            if u.fragment:
                if not f.endswith('.html'):
                    problems.append('%s: %s: an anchor on a page that is not HTML' % (where, ref_))
                elif u.fragment not in parse(f).ids:
                    problems.append('%s: %s: no id "%s" on %s' % (where, ref_, u.fragment, os.path.relpath(f, pages)))
    for path in sorted(csss):
        text = open(path, encoding='utf-8').read()
        for m in re.finditer(r'url\(\s*[\'"]?([^\'")]+)[\'"]?\s*\)', text):
            t = m.group(1)
            if t.startswith('data:') or '://' in t:
                continue
            f = resolve(pages, path, t)
            if f is None or not os.path.isfile(f):
                problems.append('%s: url(%s): no such file' % (os.path.relpath(path, pages), t))
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument('--repos')
    ap.add_argument('--ref', default='main')
    a = ap.parse_args()
    problems = check(a.root, a.repos, a.ref)
    for p in problems:
        print(p)
    print('links: %d broken' % len(problems) + ('' if a.repos else ' (GitHub links not checked: no --repos)'))
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
