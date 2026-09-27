#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Nothing of the machine the site was made on reaches the public tree.

    python3 checks/public.py [--root DIR]

Reads every text file under pages/, src/, gen/, checks/ and .github/, and
README.md, and fails on:
  - a local path: a home directory (/home/<name>, /Users/<name>, /root/), a
    path under ~/projects or ~/.cache, a Claude Code scratchpad, a file:// URL;
  - a private IPv4 address (10/8, 172.16/12, 192.168/16) or a link-local one;
    the loopback and the documentation ranges are what examples use, and
    pass;
  - localhost or 0.0.0.0 with a port;
  - a process ID written as one (pid=123, PID 123);
  - an e-mail address other than the ones Mete publishes;
  - a Claude session URL or ID;
  - the name of the machine and of the user running the check, read at run
    time, so that neither is written down here.
Each finding is printed as path:line; it exits 1 if there is any."""
import argparse, getpass, ipaddress, os, re, socket, sys

DIRS = ('pages', 'src', 'gen', 'checks', '.github')
FILES = ('README.md',)
TEXT = ('.html', '.css', '.js', '.py', '.sh', '.txt', '.md', '.yml', '.yaml', '.svg', '.json')
EMAILS_ALLOWED = {'metebalci@gmail.com'}

PATTERNS = [
    ('a home directory', re.compile(r'(?<![\w.])/(?:home|Users)/[A-Za-z0-9_.-]+|(?<![\w.])/root/')),
    ('a local path', re.compile(r'~/(?:projects|\.cache|\.claude)\b|\$HOME/(?:projects|\.cache)\b|/tmp/claude')),
    ('a file:// URL', re.compile(r'file://')),
    ('localhost with a port', re.compile(r'\b(?:localhost|0\.0\.0\.0):\d+')),
    ('a process ID', re.compile(r'\bpid[=: ]+\d+|\bPID \d+', re.I)),
    ('a Claude session', re.compile(r'claude\.ai/(?:code|chat|artifact)|session[_-]?id', re.I)),
]
IPV4 = re.compile(r'(?<![\d.])(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?![\d.])')
EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')


def local_words():
    """The machine's and the user's names, as words to refuse; a CI runner's
    are its own and harmless, and names too short or too common are left."""
    words = set()
    for w in (socket.gethostname().split('.')[0], getpass.getuser()):
        if w and len(w) >= 4 and w not in ('runner', 'root', 'localhost', 'user'):
            words.add(w.lower())
    return words


def files(root):
    for d in DIRS:
        for dp, _, fs in os.walk(os.path.join(root, d)):
            if '__pycache__' in dp:
                continue
            for f in sorted(fs):
                if f.endswith(TEXT):
                    yield os.path.join(dp, f)
    for f in FILES:
        if os.path.exists(os.path.join(root, f)):
            yield os.path.join(root, f)


def check(root, extra_words=()):
    words = local_words() | {w.lower() for w in extra_words}
    word_re = re.compile(r'\b(?:%s)\b' % '|'.join(map(re.escape, sorted(words))), re.I) if words else None
    problems = []
    for path in files(root):
        rel = os.path.relpath(path, root)
        # This file names the patterns it looks for, and nothing else.
        if rel == os.path.join('checks', 'public.py'):
            continue
        for n, line in enumerate(open(path, encoding='utf-8', errors='replace'), 1):
            for what, rx in PATTERNS:
                if rx.search(line):
                    problems.append('%s:%d: %s: %s' % (rel, n, what, rx.search(line).group(0)))
            for m in IPV4.finditer(line):
                try:
                    ip = ipaddress.IPv4Address(m.group(1))
                except ValueError:
                    continue
                if (ip.is_private or ip.is_link_local) and not ip.is_loopback \
                        and not any(ip in ipaddress.ip_network(n_) for n_ in ('192.0.2.0/24', '198.51.100.0/24', '203.0.113.0/24', '0.0.0.0/32')):
                    problems.append('%s:%d: a private address: %s' % (rel, n, ip))
            for m in EMAIL.finditer(line):
                if m.group(0).lower() not in EMAILS_ALLOWED:
                    problems.append('%s:%d: an e-mail address: %s' % (rel, n, m.group(0)))
            if word_re and word_re.search(line):
                problems.append('%s:%d: this machine\'s or this user\'s name' % (rel, n))
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    a = ap.parse_args()
    problems = check(a.root)
    for p in problems:
        print(p)
    print('public: %d finding%s' % (len(problems), '' if len(problems) == 1 else 's'))
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
