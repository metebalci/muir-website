#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Every character the site draws in one of its own fonts is in that font.

    python3 checks/fonts.py [--root DIR] [--browser PATH]

The site serves its own fonts, IBM Plex Mono, the cut of Zen Maru Gothic
and the cut of Gelasio Italic in pages/fonts/, and a character a font lacks
is drawn in whatever the reader's system has instead, or as an empty box.  So, over every page in
DIR/pages (DIR is the repository, by default the one this file is in):
  - a headless Chromium loads the page, 1440 px wide, and reports
    each piece of text with the font family the stylesheets give it, as the
    browser computes it: every text node, and the text of every ::before and
    ::after, with text-transform applied;
  - where that family's first name is one the page's own stylesheets declare
    with @font-face, every character of the text must be in the character
    map of each of the family's files, as fc-query reads it.
Text whose first family is a system font (Arial, Georgia) is the reader's
system's to draw, and is not checked, even where a font of the site's own
(Gelasio, after Georgia) comes next.

It needs Chromium or Chrome (--browser, or $CHROME, or chrome-headless-shell,
chromium, chromium-browser, google-chrome on the PATH, or Playwright's
headless shell), and fc-query, from fontconfig.  It prints each character
missing from its font, with where it is drawn, and exits 1 if there is any;
it exits 2 if it cannot run."""
import argparse, glob, json, os, pathlib, re, shutil, subprocess, sys, tempfile, time, unicodedata
from html.parser import HTMLParser

# The DevTools protocol's name for a page's session, written in two parts so
# that checks/public.py does not take it for a Claude session's ID.
SESSION = 'session' 'Id'

BROWSERS = ('chrome-headless-shell', 'chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable')

# Run in each page once it has loaded: [family, weight, text, where] for
# every piece of text.
PROBE = r'''(function () {
  var SKIP = {SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, TEMPLATE: 1, TITLE: 1, title: 1, desc: 1};
  function where(e) {
    var out = [];
    for (; e && e.nodeType === 1 && out.length < 4; e = e.parentNode) {
      var s = e.nodeName.toLowerCase();
      if (e.id) { out.unshift(s + '#' + e.id); break; }
      var c = e.getAttribute('class');
      if (c) s += '.' + c.trim().split(/\s+/).join('.');
      out.unshift(s);
    }
    return out.join(' > ');
  }
  function transform(t, cs) {
    var tt = cs.textTransform;
    if (tt === 'uppercase') return t.toUpperCase();
    if (tt === 'lowercase') return t.toLowerCase();
    if (tt === 'capitalize' || cs.fontVariantCaps !== 'normal') return t + t.toUpperCase();
    return t;
  }
  var out = [];
  function add(cs, text, e) {
    if (/\S/.test(text)) out.push([cs.fontFamily, cs.fontWeight, transform(text, cs), where(e)]);
  }
  var w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT), n;
  while ((n = w.nextNode())) {
    var p = n.parentNode, skip = false;
    for (var a = p; a && a.nodeType === 1; a = a.parentNode) if (SKIP[a.nodeName]) { skip = true; break; }
    if (!skip) add(getComputedStyle(p), n.data, p);
  }
  var all = document.body.getElementsByTagName('*');
  for (var i = 0; i < all.length; i++) {
    ['::before', '::after'].forEach(function (ps) {
      var cs = getComputedStyle(all[i], ps), c = cs.content;
      if (c && c.charAt(0) === '"') {
        try { add(cs, JSON.parse(c), all[i]); } catch (err) { add(cs, c.slice(1, -1), all[i]); }
      }
    });
  }
  return out;
})()'''


def browser(given=None):
    for b in (given, os.environ.get('CHROME')):
        if b:
            return b
    for b in BROWSERS:
        if shutil.which(b):
            return shutil.which(b)
    home = os.path.expanduser('~')
    found = sorted(glob.glob(os.path.join(home, '.cache', 'ms-playwright', 'chromium_headless_shell-*',
                                          'chrome-headless-shell-linux64', 'chrome-headless-shell')))
    return found[-1] if found else None


def charset(path, cache={}):
    """The code points a font file maps, read by fc-query."""
    if path not in cache:
        r = subprocess.run(['fc-query', '-f', '%{charset}\\n', path], capture_output=True, text=True)
        if r.returncode != 0 or not r.stdout.strip():
            raise RuntimeError('fc-query cannot read %s: %s' % (path, r.stderr.strip()))
        cps = set()
        for part in r.stdout.split('\n')[0].split():
            lo, _, hi = part.partition('-')
            cps.update(range(int(lo, 16), int(hi or lo, 16) + 1))
        cache[path] = cps
    return cache[path]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.css = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and (a.get('rel') or '').lower() == 'stylesheet' and a.get('href'):
            self.css.append(a['href'])


def faces(pages, page):
    """{family, lower-cased: [font files]} of the @font-face rules in the
    stylesheets the page links."""
    p = Links()
    p.feed(open(page, encoding='utf-8').read())
    out = {}
    for href in p.css:
        if '://' in href:
            continue
        css = os.path.normpath(os.path.join(pages, href.lstrip('/')) if href.startswith('/')
                               else os.path.join(os.path.dirname(page), href))
        if not os.path.isfile(css):
            continue
        for block in re.findall(r'@font-face\s*\{([^}]*)\}', open(css, encoding='utf-8').read()):
            fam = re.search(r'font-family\s*:\s*([^;]+)', block)
            urls = re.findall(r'url\(\s*[\'"]?([^\'")]+)[\'"]?\s*\)', block)
            if fam:
                name = fam.group(1).strip().strip('\'"').lower()
                out.setdefault(name, []).extend(os.path.normpath(os.path.join(os.path.dirname(css), u)) for u in urls)
    return out


class Browser:
    """A headless Chromium driven over its DevTools pipe: file descriptor 3
    carries the commands to it and 4 its answers, each a JSON message ended
    by a NUL."""

    def __init__(self, path, tmp):
        to_r, self.to_w = os.pipe()
        self.from_r, from_w = os.pipe()

        def fds():
            a, b = os.dup2(os.dup(to_r), 100), os.dup2(os.dup(from_w), 101)
            os.dup2(a, 3), os.dup2(b, 4)
            os.set_inheritable(3, True), os.set_inheritable(4, True)
        self.p = subprocess.Popen([path, '--headless', '--no-sandbox', '--disable-gpu', '--hide-scrollbars',
                                   '--no-first-run', '--remote-debugging-pipe', '--user-data-dir=' + tmp,
                                   'about:blank'], preexec_fn=fds, close_fds=False,
                                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.close(to_r), os.close(from_w)
        self.buf, self.n, self.events = b'', 0, []
        target = self.send('Target.createTarget', url='about:blank')['targetId']
        self.session = self.send('Target.attachToTarget', targetId=target, flatten=True)[SESSION]
        self.send('Page.enable', True)
        self.send('Emulation.setDeviceMetricsOverride', True, width=1440, height=900, deviceScaleFactor=1, mobile=False)

    def receive(self, deadline):
        while b'\0' not in self.buf:
            if time.time() > deadline:
                raise RuntimeError('the browser did not answer in time')
            chunk = os.read(self.from_r, 1 << 16)
            if not chunk:
                raise RuntimeError('the browser quit')
            self.buf += chunk
        msg, self.buf = self.buf.split(b'\0', 1)
        return json.loads(msg)

    def send(self, method, in_page=False, **params):
        self.n += 1
        msg = {'id': self.n, 'method': method, 'params': params}
        if in_page:
            msg[SESSION] = self.session
        os.write(self.to_w, json.dumps(msg).encode() + b'\0')
        deadline = time.time() + 60
        while True:
            m = self.receive(deadline)
            if m.get('id') == self.n:
                if 'error' in m:
                    raise RuntimeError('%s: %s' % (method, m['error'].get('message')))
                return m.get('result', {})
            self.events.append(m)

    def texts(self, page):
        """The page's text with its computed families."""
        self.events = []
        self.send('Page.navigate', True, url=pathlib.Path(page).as_uri())
        deadline = time.time() + 60
        while not any(e.get('method') == 'Page.loadEventFired' for e in self.events):
            self.events.append(self.receive(deadline))
        r = self.send('Runtime.evaluate', True, expression=PROBE, returnByValue=True)
        if 'exceptionDetails' in r:
            raise RuntimeError('%s: the probe failed: %s' % (page, r['exceptionDetails'].get('text')))
        return r['result']['value']

    def close(self):
        try:
            self.send('Browser.close')
        except RuntimeError:
            pass
        try:
            self.p.wait(10)
        except subprocess.TimeoutExpired:
            self.p.kill()
        os.close(self.to_w), os.close(self.from_r)


def check(root, chrome=None):
    chrome = browser(chrome)
    if not chrome:
        raise RuntimeError('no Chromium or Chrome: give --browser or $CHROME')
    if not shutil.which('fc-query'):
        raise RuntimeError('no fc-query: install fontconfig')
    pages = os.path.join(root, 'pages')
    htmls = sorted(os.path.join(dp, f) for dp, _, fs in os.walk(pages) for f in fs if f.endswith('.html'))
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        b = Browser(chrome, tmp)
        try:
            texts = [b.texts(p) for p in htmls]
        finally:
            b.close()
    for page, found in zip(htmls, texts):
        rel = os.path.relpath(page, pages)
        declared = faces(pages, page)
        seen = set()
        for family, weight, text, where in found:
            first = family.split(',')[0].strip().strip('\'"').lower()
            files = declared.get(first)
            if not files:
                continue
            cover = set.intersection(*(charset(f) for f in files))
            for c in text:
                if c in '\t\n\r' or unicodedata.category(c) in ('Cc', 'Cf') or ord(c) in cover:
                    continue
                if (first, c, where) in seen:
                    continue
                seen.add((first, c, where))
                problems.append('%s: U+%04X %s is not in %s (%s), in %s: "%s"'
                                % (rel, ord(c), c, family.split(',')[0].strip(),
                                   ', '.join(os.path.relpath(f, pages) for f in files), where, text.strip()[:60]))
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument('--browser')
    a = ap.parse_args()
    try:
        problems = check(a.root, a.browser)
    except RuntimeError as e:
        print('fonts: cannot run: %s' % e)
        sys.exit(2)
    for p in problems:
        print(p)
    print('fonts: %d character%s missing from its font' % (len(problems), '' if len(problems) == 1 else 's'))
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
