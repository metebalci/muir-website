#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Each check is shown able to fail before it is trusted.

    python3 checks/test_checks.py [--repos DIR] [--ref REF]

Copies the repository into a scratch directory, runs every check on the
copy as it is (each must pass), then plants one fault at a time, runs the
check that should catch it, and requires it to fail; each fault is taken
back out before the next.  With --repos the GitHub part of the link check
is tested too, and the check of the projects' links into the site, on a
scratch clone of muir-sim given a commit that plants the fault.  The font
check needs what checks/fonts.py needs, a browser and fc-query.  It prints one line a fault and exits 1 if a check passed a
fault or failed the clean copy."""
import argparse, os, shutil, socket, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fonts, generated, links, public, sitelinks  # noqa: E402

COPY = ('pages', 'src', 'gen', 'checks', '.github', 'README.md')


def edit(path, old, new):
    s = open(path, encoding='utf-8').read()
    assert s.count(old) >= 1, (path, old)
    open(path, 'w', encoding='utf-8').write(s.replace(old, new, 1))


def git(repo, *args, stdin=None):
    env = dict(os.environ, GIT_AUTHOR_NAME='test_checks', GIT_AUTHOR_EMAIL='',
               GIT_COMMITTER_NAME='test_checks', GIT_COMMITTER_EMAIL='',
               GIT_INDEX_FILE=os.path.join(repo, '.git', 'test_checks-index'))
    r = subprocess.run(['git', '-C', repo] + list(args), input=stdin, capture_output=True, text=True, env=env, check=True)
    return r.stdout.strip()


def plant_commit(repo, ref, path, text):
    """Moves ref in the scratch clone to a new commit on top of it that adds
    `path` holding `text`; gives back the commit ref was at."""
    old = git(repo, 'rev-parse', ref)
    blob = git(repo, 'hash-object', '-w', '--stdin', stdin=text)
    git(repo, 'read-tree', old)
    git(repo, 'update-index', '--add', '--cacheinfo', '100644,%s,%s' % (blob, path))
    new = git(repo, 'commit-tree', git(repo, 'write-tree'), '-p', old, '-m', 'a planted fault')
    git(repo, 'update-ref', 'refs/heads/' + ref, new)
    return old


def safely(run):
    """A check that cannot run fails, with why."""
    try:
        return run()
    except (RuntimeError, OSError, subprocess.SubprocessError) as e:
        return ['cannot run: %s' % e]


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
            'fonts': lambda: safely(lambda: fonts.check(root)),
        }
        if a.repos:
            # The four clones, muir-sim's a scratch clone of the one given,
            # so that a fault can be committed to it.
            repos = os.path.join(tmp, 'repos')
            os.makedirs(repos)
            for r in sitelinks.REPOS:
                if r == 'muir-sim':
                    subprocess.run(['git', 'clone', '--quiet', '--shared', '--no-checkout',
                                    os.path.join(os.path.abspath(a.repos), r), os.path.join(repos, r)], check=True)
                    git(os.path.join(repos, r), 'update-ref', 'refs/heads/' + a.ref, 'refs/remotes/origin/' + a.ref)
                elif os.path.isdir(os.path.join(a.repos, r)):
                    os.symlink(os.path.abspath(os.path.join(a.repos, r)), os.path.join(repos, r))
            runs['sitelinks'] = lambda: safely(lambda: sitelinks.check(root, repos, a.ref))
        for name, run in runs.items():
            got = run()
            ok = not got
            failed += not ok
            print('%-9s the clean copy passes: %s%s' % (name, 'yes' if ok else 'NO', '' if ok else ' ' + '; '.join(got[:3])))

        faults = [
            ('links', 'a link to a page that does not exist',
             P('pages', 'index.html'), 'href="quux/"', 'href="quux-gone/"'),
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
            ('public', 'a private address at the end of a sentence',
             P('README.md'), '# muir-website', '# muir-website\n\nBoot from 10.' + '0.0.5.'),
            ('public', 'an e-mail address in the README',
             P('README.md'), '# muir-website', '# muir-website\n\nWrite to someone' + '@' + 'example.org.'),
            ('public', 'this machine\'s name in a page',
             P('pages', 'index.html'), '<main id="main">', '<main id="main"><!-- built on %s -->' % socket.gethostname().split('.')[0]),
            ('generated', 'a fit figure changed in the generator and not built',
             P('gen', 'fpga', 'gen.py'), "('CADR', 15050, 53200, 'LUTs', 46, 140", "('CADR', 15051, 53200, 'LUTs', 46, 140"),
            ('generated', 'a page edited by hand',
             P('pages', 'system', 'index.html'), '<h3>It evolves the system</h3>', '<h3>It evolved the system</h3>'),
            ('generated', 'a page nothing builds',
             P('pages', 'fpga', 'index.html'), None, 'full-page.html'),
            ('fonts', 'a katakana outside the cut in a drawing label',
             P('pages', 'cadr', 'index.html'), '>the machine, whole</text>', '>the machine, whole \u30b3</text>'),
            ('fonts', 'a character outside Plex in a pre',
             P('pages', 'ozd', 'index.html'), '<pre>asking 3060 at', '<pre>asking \u29c9 3060 at'),
        ]
        if a.repos:
            faults += [
                ('links', 'a GitHub path not in the repository',
                 P('pages', 'index.html'), 'muir-sim/blob/main/docs/quux.md"', 'muir-sim/blob/main/docs/quux-gone.md"'),
                ('links', 'a Markdown heading that is not there',
                 P('pages', 'index.html'), 'muir-sim/blob/main/docs/sources.md"', 'muir-sim/blob/main/docs/sources.md#no-such-heading"'),
                ('links', 'a GitHub path not on the cadr branch',
                 P('pages', 'system', 'index.html'), 'muir-sys/tree/cadr"', 'muir-sys/blob/cadr/docs/no-such.md"'),
                ('links', 'a GitHub path not at a release tag',
                 P('pages', 'system', 'releases.html'), 'muir-sys/blob/release-1002/docs/release-1002.md"', 'muir-sys/blob/release-1002/docs/release-2000.md"'),
                ('links', 'a branch or tag the repository does not have',
                 P('pages', 'system', 'index.html'), 'muir-sys/tree/cadr"', 'muir-sys/tree/cadr-gone"'),
                ('links', 'a release tag the repository does not have',
                 P('pages', 'system', 'index.html'), 'muir-sys/releases/tag/release-1002"', 'muir-sys/releases/tag/release-1009"'),
                ('sitelinks', 'a line in muir-sim linking muir.metebalci.com/simulator/#no-such',
                 'muir-sim', 'PLANTED.md', 'See <https://muir.metebalci.com/simulator/#no-such>.\n'),
                ('sitelinks', 'a line in muir-sim linking a page the site does not have',
                 'muir-sim', 'docs/planted.md', 'The [manual](https://muir.metebalci.com/simulator/manual.html).\n'),
                ('sitelinks', 'a line in muir-sim linking a retired site',
                 'muir-sim', 'PLANTED.md', 'The pages: https://ozd.metebalci.com/\n'),
            ]
        for name, what, path, old, new in faults:
            if name == 'sitelinks':
                # A commit in the scratch clone, taken back out after.
                clone = os.path.join(repos, path)
                was = plant_commit(clone, a.ref, old, new)
                got = runs[name]()
                git(clone, 'update-ref', 'refs/heads/' + a.ref, was)
            elif old is None:
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
