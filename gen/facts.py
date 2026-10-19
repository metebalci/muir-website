# SPDX-License-Identifier: AGPL-3.0-or-later
"""The figures that differ from board to board, each written once.

Each figure is here and only here.  It covers each board's display, QUUX's
period, cache and main memory on each board, the main memory a released
QUUX card offers, each fit's figures with the commit it was built from, and
Linux's share of the board's memory.  Two places read it:

  - the pages written by hand in src/, through gen/build.py, which replaces
    each {{name}} with token(name); TOKENS lists the names;
  - gen/fpga/gen.py's drawings and pages, which import this module.

checks/facts.py builds the site with every figure here changed
(MUIR_SITE_FACTS_PERTURB=1, below).  It fails if a page still states one of
the real figures, since that figure was written by hand.

Where each figure was read is in the site's gitignored notes, not here.
"""
import os

# With MUIR_SITE_FACTS_PERTURB=1 every number below is moved by 7, so that a
# page built from this module carries none of the real figures.
PERTURB = os.environ.get('MUIR_SITE_FACTS_PERTURB') == '1'


def _n(v):
    return v + 7 if PERTURB else v


# The boards, in the site's order.  `short` is the name a token starts with.
BOARDS = ('arty-z7-20', 'kria-kr260', 'de25-nano')
SHORT = {'arty-z7-20': 'arty', 'kria-kr260': 'kria', 'de25-nano': 'de25'}
NAME = {'arty-z7-20': 'Arty Z7-20', 'kria-kr260': 'Kria KR260', 'de25-nano': 'DE25-Nano'}

# Each board's display: the connector and the size of the picture, which both
# machines show at 60 Hz.
DISPLAY = {
    'arty-z7-20': ('HDMI', _n(1280), _n(1024)),
    'kria-kr260': ('DisplayPort', _n(1920), _n(1080)),
    'de25-nano': ('HDMI', _n(1280), _n(1024)),
}

# QUUX on each board that runs it, as its bitstream is built: the clock's
# period in ns, the cache in words, main memory in megawords.
QUUX = {
    'arty-z7-20': dict(period=_n(48), cache=_n(4096), memory=_n(32)),
    'kria-kr260': dict(period=_n(19), cache=_n(65536), memory=_n(32)),
    'de25-nano': dict(period=_n(22.5), cache=_n(16384), memory=_n(32)),
}

# The most main memory `--main-memory-size` gives QUUX on a released card,
# in megawords; 32 is the default on every board.
CARD_MEMORY_MOST = {'arty-z7-20': _n(32), 'kria-kr260': _n(32), 'de25-nano': _n(64)}
CARD_MEMORY_DEFAULT = _n(32)


class Fit:
    """One fit of one machine on one board: the logic used of the part's,
    in the part's own unit; the block memory used of the part's, in blocks
    of `block_kb` KB each; the Kria KR260's UltraRAM where there is one; the
    worst setup slack in ns; and the commit the fit was built from."""
    def __init__(self, logic, logic_total, logic_unit, memory, memory_total, memory_unit, block_kb,
                 setup, commit, uram=None):
        self.logic, self.logic_total, self.logic_unit = _n(logic), logic_total, logic_unit
        self.memory, self.memory_total, self.memory_unit = _n(memory), memory_total, memory_unit
        self.block_kb, self.setup, self.commit = block_kb, _n(setup), commit
        self.uram = (_n(uram[0]), uram[1]) if uram else None


# The fits the site shows: the CADR's are the ones its released cards are
# built from; QUUX's are its design's, from clean trees.  The DE25-Nano's
# logic is Quartus's ALMs used in final placement.  The Kria KR260's CADR
# uses no UltraRAM, which its row shows as 0 of 64.
FITS = {
    ('arty-z7-20', 'cadr'): Fit(15187, 53200, 'LUTs', 46, 140, 'BRAM', 4.5, 0.275, 'c3b8fd2'),
    ('kria-kr260', 'cadr'): Fit(15309, 117120, 'LUTs', 41, 144, 'BRAM', 4.5, 1.987, 'c3b8fd2', uram=(0, 64)),
    ('de25-nano', 'cadr'): Fit(18108, 46800, 'ALMs', 135, 358, 'M20K', 2.5, 2.353, 'c3b8fd2'),
    ('arty-z7-20', 'quux'): Fit(28766, 53200, 'LUTs', 96, 140, 'BRAM', 4.5, 0.493, 'aa4a6ad'),
    ('kria-kr260', 'quux'): Fit(31622, 117120, 'LUTs', 43.5, 144, 'BRAM', 4.5, 0.013, 'f4df742', uram=(14, 64)),
    ('de25-nano', 'quux'): Fit(35063, 46800, 'ALMs', 162, 358, 'M20K', 2.5, 0.002, 'b1b4bcb'),
}

# Linux's share of the board's memory: with the CADR's areas reserved (kB),
# and with QUUX's region reserved (the figure and its unit).
LINUX_CADR_KB = {'arty-z7-20': _n(493976), 'kria-kr260': _n(3990556),
                 'de25-nano': _n(938276)}
LINUX_QUUX = {'arty-z7-20': (_n(350.875), 'MB'), 'kria-kr260': (_n(3843388), 'kB'),
              'de25-nano': (_n(670.875), 'MB')}


# ---------------------------------------------------------------- formatting

def num(v):
    """A number as the pages write it: thousands grouped, no trailing zero."""
    if isinstance(v, float) and not v.is_integer():
        s = ('%.3f' % v).rstrip('0').rstrip('.')
        whole, _, frac = s.partition('.')
        return format(int(whole), ',') + ('.' + frac if frac else '')
    return format(int(v), ',')


def period(board):
    """'19': QUUX's period on the board, in ns."""
    return num(QUUX[board]['period'])


def mhz(board):
    """'52.6': QUUX's clock frequency on the board, in MHz, from its period."""
    return num(round(1000 / QUUX[board]['period'], 1))


def cache_k(board):
    """'64K': QUUX's cache on the board, in K words where it is a whole K."""
    w = QUUX[board]['cache']
    return '%dK' % (w // 1024) if w % 1024 == 0 else num(w)


def cache_words(board):
    """'65,536': QUUX's cache on the board, in words."""
    return num(QUUX[board]['cache'])


def display(board, sep=' by '):
    _, w, h = DISPLAY[board]
    return '%d%s%d' % (w, sep, h)


def memory(board):
    return '%dMW' % QUUX[board]['memory']


def linux_quux(board):
    v, unit = LINUX_QUUX[board]
    return '%s %s' % (num(v), unit)


def fit(board, machine):
    return FITS[(board, machine)]


def logic_label(f):
    """'LUTs 15,187 of 53,200', as the drawings label the fabric's first bar."""
    return '%s %s of %s' % ('ALM' if f.logic_unit == 'ALMs' else f.logic_unit, num(f.logic), num(f.logic_total))


def memory_label(f):
    """'BRAM 207 KB of 630 KB', the second bar's label."""
    return '%s %s KB of %s KB' % (f.memory_unit, num(f.memory * f.block_kb), num(f.memory_total * f.block_kb))


def uram_label(f):
    return 'URAM %d of %d' % f.uram


def fit_rows(f):
    """The bars a drawing draws for a fit: (label, the fraction used)."""
    rows = [(logic_label(f), f.logic / f.logic_total), (memory_label(f), f.memory / f.memory_total)]
    if f.uram:
        rows.append((uram_label(f), f.uram[0] / f.uram[1]))
    return rows


def setup(f):
    """'+0.275', the worst setup slack, signed."""
    return '+%s' % ('%.3f' % f.setup)


def percent(used, total):
    return '%.1f' % (100.0 * used / total)


# ---------------------------------------------------------------- tokens

def _tokens():
    t = {}
    for b in BOARDS:
        s = SHORT[b]
        t[s + '.name'] = NAME[b]
        if b in DISPLAY:
            t[s + '.output'] = DISPLAY[b][0]
            t[s + '.display'] = display(b)
            t[s + '.display.x'] = display(b, '&times;')
        if b in QUUX:
            t[s + '.period'] = period(b) + '&nbsp;ns'
            t[s + '.cache'] = cache_k(b) + ' words'
            t[s + '.cache.k'] = cache_k(b)
            t[s + '.memory'] = memory(b)
    caches = sorted(QUUX, key=lambda b: QUUX[b]['cache'])
    t['quux.cache.least'] = cache_k(caches[0])
    t['quux.cache.most'] = cache_k(caches[-1])
    return t


TOKENS = _tokens()


def token(name):
    """The text a {{name}} in a src/ page stands for; an unknown name stops the build."""
    if name not in TOKENS:
        raise KeyError('{{%s}}: no such figure in gen/facts.py' % name)
    return TOKENS[name]
