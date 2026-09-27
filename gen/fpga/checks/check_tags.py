#!/usr/bin/env python3
"""Tags balance, and every link on every page resolves."""
import os, re, sys
from html.parser import HTMLParser
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'pages', 'fpga')
VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
bad = 0
class P(HTMLParser):
    def __init__(s):
        super().__init__(convert_charrefs=False); s.stack=[]; s.err=[]
    def handle_starttag(s,t,a):
        if t not in VOID: s.stack.append((t,s.getpos()))
    def handle_startendtag(s,t,a): pass
    def handle_endtag(s,t):
        if not s.stack: s.err.append('stray </%s> at %s' % (t,s.getpos())); return
        top,pos = s.stack.pop()
        if top != t: s.err.append('</%s> closes <%s> opened at %s (at %s)' % (t,top,pos,s.getpos()))
for f in sorted(os.listdir(D)):
    if not f.endswith('.html'): continue
    t = open(os.path.join(D,f)).read()
    p = P(); p.feed(t); p.close()
    if p.stack: p.err.append('unclosed: %s' % [x[0] for x in p.stack])
    for e in p.err: print('%s: %s' % (f,e)); bad += 1
    for href in re.findall(r'href="([^"]+)"', t):
        if href.startswith(('http://','https://','mailto:')): continue
        target = href.split('#')[0]
        if target and not os.path.exists(os.path.join(D,target)):
            print('%s: dead link %s' % (f,href)); bad += 1
    # every id an anchor points at
    ids = set(re.findall(r'id="([^"]+)"', t))
    for href in re.findall(r'href="#([^"]+)"', t):
        if href not in ids: print('%s: dead anchor #%s' % (f,href)); bad += 1
print('tags and links:', 'OK' if not bad else '%d problem(s)' % bad)
sys.exit(1 if bad else 0)
