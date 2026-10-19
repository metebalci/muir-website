#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Writes muir-fpga's pages of the site, pages/fpga/, in the site's hand.
Every drawing is lifted byte for byte out of the base pages in base/, which
are muir-fpga's pages as they were drawn, and changed only by the
substitutions below, so no drawing can change by accident here.  Run it
through gen/build.py, which builds the whole site; `python3 gen.py <dir>`
writes these pages alone into <dir>."""
import os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, 'base')
sys.path.insert(0, os.path.dirname(HERE))
import chrome  # noqa: E402
import facts as F  # noqa: E402
import fit  # noqa: E402
OUT = None     # set by main()

# THE MAKERS' OWN PAGES FOR THE BOARDS.  Each was opened in a browser and read to
# be that board's product page before it was written here: Digilent's "Arty Z7:
# Zynq-7000 SoC Development Board", whose options are the Arty Z7-20 and the
# Arty Z7-10; and Terasic's "DE25-Nano
# Development and Education Board", whose specifications give the FPGA as
# A5EB013BB23BE4SCS.  The ampersands are written as HTML wants them.
DIGILENT_ARTY = 'https://digilent.com/shop/arty-z7-zynq-7000-soc-development-board/'
AMD_KR260 = 'https://www.amd.com/en/products/system-on-modules/kria/k26/kr260-robotics-starter-kit.html'
TERASIC_DE25 = 'https://www.terasic.com.tw/cgi-bin/page/archive.pl?Language=English&amp;CategoryNo=115&amp;No=1384'

def svgs(page):
    t = open(os.path.join(BASE, page)).read()
    return re.findall(r'<svg\b.*?</svg>', t, re.S)

def sub(text, old, new, count=1):
    """Replace a figure, asserting it appears exactly as often as expected, so
    a drawing that has moved under the generator stops the run."""
    n = text.count(old)
    assert n == count, (old[:80], n, count)
    return text.replace(old, new)

# THE FIT FIGURES ON THE DRAWINGS, from each board's own place and route
# report.  The Arty Z7-20 was built from a clean tree at 9d1cf26, whose
# bitstreams' stamps read 9d1cf260.  The lifted drawings carry the figures of
# older builds, and these replacements move the labels, the bars that draw the
# same per cent, the aria-labels and the comments beside the labels, and
# nothing else.  The old three-line timing block under the fabric's label ---
# the clock rate, the worst slack and the failing-endpoint count, with an empty
# bar under them --- comes off instead of being moved: the clock is already
# stated in the clock block, and the two entries below each drop that whole
# clause, in the labels and in the aria-label, rather than update it.  One
# line of it returns as slack_block() below.
#
# THE WORST SETUP SLACK, one line under the two resource bars, the same on
# every board's drawing.  It is the worst value and nothing else: one number a
# board, at the resource labels' own x and on the 36-unit row pitch the two
# bars keep (68, 104, 140), in the same class and size as the labels above it,
# and written in the drawing's own shape for this measurement --- the name,
# then the signed number with a space before its unit, as "BRAM 207 KB of
# 630 KB" writes its own.
def slack_block(ns, y=140):
    """The comment and the one label, to stand under a drawing's last bar.
    No leading or trailing newline: the caller joins it to the line above."""
    return ('          <!-- The worst setup slack of that build, and only the worst\n'
            '               value: the rest of what the fit reported about timing is\n'
            '               in docs/fits.md of muir-fpga and is not drawn.  It sits\n'
            '               on the same row pitch the two bars keep and carries no\n'
            '               bar of its own, because a slack has no total to be a\n'
            '               fraction of. -->\n'
            '          <text class="d-s" x="-164" y="%d">worst setup %s ns</text>' % (y, ns))

# THE MEMORY BOXES under the chip.  The CADR reserves 16 MB of main memory,
# 1 MB for the display and 128 KB for the disk pack program's records, the
# same on every board, and Linux has the rest.  QUUX has its own region: its
# main memory, packed, directly below the display.  Linux's share and QUUX's
# main memory are gen/facts.py's.
MEM_OLD = """          <text class="d-s" x="87" y="762" text-anchor="middle">64 MB reserved for main memory,</text>
          <text class="d-s" x="87" y="776" text-anchor="middle">8 MB for the display, 56 MB spare</text>
          <text class="d-s" x="87" y="790" text-anchor="middle">&mdash; and 384 MB left to Linux</text>
"""
LONG = {'arty': 'arty-z7-20', 'kria': 'kria-kr260', 'de25': 'de25-nano'}
def mem_block(board, quux=False, own=False):
    b = LONG[board]
    if own:
        l1, l2 = 'QUUX&rsquo;s areas:', '%s main memory, 1 MB display, 128 KB packs' % F.memory(b)
        l3 = '&mdash; and Linux has the rest, %s' % F.linux_quux(b)
    elif quux:
        l1, l2 = 'the CADR&rsquo;s areas, which QUUX shares:', '16 MB main memory, 1 MB display, 128 KB packs'
        l3 = '&mdash; and Linux has the rest, %s kB' % F.num(F.LINUX_CADR_KB[b])
    else:
        l1, l2 = '16 MB reserved for main memory,', '1 MB for the display, 128 KB for disk packs'
        l3 = '&mdash; and Linux has the rest, %s kB' % F.num(F.LINUX_CADR_KB[b])
    return ''.join('          <text class="d-s" x="87" y="%d" text-anchor="middle">%s</text>\n' % (y, s)
                   for y, s in ((762, l1), (776, l2), (790, l3)))

# THE FIT UNDER THE FABRIC'S LABEL on a CADR drawing: a bar for the logic and
# one for the block memory, and the worst setup slack under them, every
# figure gen/facts.py's.  The base drawings' own figures, their comment and
# their old three-line timing block, from FIT_FROM to FIT_TO, come off.
FIT_FROM = '          <!-- What the machine costs on '
FIT_TO = '          <text class="d-n" x="-158" y="192">0%</text>\n'
FIT_NOTE = ('          <!-- The fit: what the machine costs on the part, a bar for the\n'
            '               logic and one for the block memory, and the worst setup slack\n'
            '               under them, all from gen/facts.py. -->\n')
def cadr_fit_block(board):
    f = F.fit(board, 'cadr')
    return FIT_NOTE + fit_bars(F.fit_rows(f)) + slack_block(F.setup(f)) + '\n'

def fit_span(svg):
    """Where a drawing's fit bars and slack stand: from the first bar's label
    to the end of the slack's line."""
    i = svg.index('          <text class="d-s" x="-164" y="68">')
    assert svg.count('>worst setup ') == 1
    j = svg.index('\n', svg.index('>worst setup ')) + 1
    return i, j

def cadr_fit_words(board, unit='lookup tables', memory='block RAM'):
    """The fit, as a CADR drawing's aria-label says it."""
    f = F.fit(board, 'cadr')
    more = ('; and %s of the %s UltraRAM blocks in use, %s per cent' % (F.num(f.uram[0]), F.num(f.uram[1]), F.percent(*f.uram))
            if f.uram else '')
    return ('%s of the %s %s in use, %s per cent; and %s KB of the %s KB of %s, %s per cent%s. '
            'Under those %s figures, the worst setup slack of this build, plus %s nanoseconds.'
            % (F.num(f.logic), F.num(f.logic_total), unit, F.percent(f.logic, f.logic_total),
               F.num(f.memory * f.block_kb), F.num(f.memory_total * f.block_kb), memory,
               F.percent(f.memory, f.memory_total), more, 'three' if f.uram else 'two', F.setup(f).lstrip('+')))

# What a drawing's aria-label says of ozd, which runs on every board's own
# Linux (each board's Buildroot carries it, and the released fpgarc points
# the Chaosnet at it on the loopback).
OZD_ON_BOARD = 'ozd runs on this board&rsquo;s own Linux, so a card by itself is a whole site.'

# The Arty Z7-20's drawing as the base page has
# it, changed: the chip's label, the memory box, the aria-label's words for
# the fit (cadr_fit_words) and for ozd, and the fit itself, which
# board_svg() replaces whole (cadr_fit_block).
OZD_BASE = ("ozd runs on a host of its own today, and running it on this board's own processing system, so that a card by itself is a whole site, "
            "is built and has been started on no board: no line reaches the block, because a line would say there is a path on this board and there is none yet.")
ARTY_FIT = [
    ('The CADR mapped onto one XC7Z020.', 'The CADR mapped onto one AMD Zynq 7020, part XC7Z020-1CLG400C.'),
    ('5,441 of the 13,300 slices occupied, 40.9 per cent, which is a conservative figure since a fuller design packs tighter; and 205 KB of the 630 KB of block RAM, 32.5 per cent; and the timing of this build, which is met --- the fabric runs at 100 megahertz with a tick of 10 nanoseconds, worst slack plus 0.176 nanoseconds against that, and none of its 54,072 endpoints failing. ',
     cadr_fit_words('arty-z7-20') + ' '),
    (OZD_BASE, OZD_ON_BOARD),
    ("the file and time host the band calls being another machine on that network, from which",
     "the associated machine the band calls being ozd on the board, from which"),
    (MEM_OLD, mem_block('arty')),
]
# MIT'S GRID MOVED FROM 5 ns TO 10 ns at 9d1cf26, and the drawings' clock
# label and aria-labels were moved with it on the pages themselves.  These
# follow them, so the generator regenerates what is committed.
GRID_10 = [
    ('<text class="d-s" x="96" y="176" text-anchor="middle">29 ticks = 290 ns</text>',
     '<text class="d-s" x="96" y="176" text-anchor="middle">15 ticks=150 ns</text>'),
    ('runs at 100 MHz, 29 ticks to the microcycle, 290 nanoseconds of real time',
     'runs at 100 MHz, 15 ticks to the microcycle, 150 nanoseconds of real time'),
    ('for the 145 the drawings name', 'for the 145 the schematics name'),
]
# THE FABRIC'S LABEL on the Zynq drawing names the programmable logic in
# words, where the drawings had "PL &mdash; fabric".  The DE25-Nano's drawing is
# generated from the Arty Z7-20's, so it starts from this label and replaces it
# with its own (de25_svg).
FABRIC_LABEL = [
    ('<text class="d-s" x="-164" y="48">PL &mdash; fabric</text>',
     '<text class="d-s" x="-164" y="48">Programmable Logic</text>'),
]
ARTY_FIT += GRID_10 + FABRIC_LABEL + [
    ("muir's simpletv tick for tick over 77 million ticks", "muir's simpletv tick for tick over 39 million ticks"),
]

# THE TWO SCREENS MOVED TO THE RASTER'S TWO EDGES, AND THREE VIDEO MODES
# BECAME ONE.  Both landed at ad86f45 and the base drawing still describes the
# world before it.
#
# THE PLACEMENT, from `rtl/plumbing/cadr_display_out.sv` lines 53-66 and its
# own localparams at 493-501: MX0 is 0 and CX0 is H_ACTIVE minus CPIC_W, so
# with a 1280-wide raster the first display holds columns 0 to 767 and the
# color board 704 to 1279.  They share 768 + 576 - 1280, which is 64 columns,
# and turned, where the widths are the heights, 963 + 454 - 1280, which is
# 137.  The color board is drawn over the first where they meet.  Before this
# both were centered on one point, and the color board's 576 by 454 fell
# wholly inside the first display's 768 by 963 and hid that part of it.
# `docs/display-output.md` lines 53-70 carries the same figures.
#
# THE MODE.  ad86f45 deleted the MODE parameter, HDMI_MODE and the card's
# `--hdmi-mode` line, so there is one mode in the fabric and nothing selects
# it: VESA DMT's 1280x1024 at 60 Hz on a 108 MHz pixel clock
# (`docs/display-output.md` lines 106-126).  THE CONSOLE NO LONGER REPORTS THE
# MODE EITHER --- `cons_hdmi_mode_name`, the enum and the word's mode field all
# went with it --- so the sentence that said it does comes off rather than
# being reworded.  The 5:4 sentence is the document's own, and it is the cost
# that was stated before the mode was fixed.
#
# The monitor readings on both boards were taken before the screens moved, so
# every sentence that rests on one says which build it was of, as
# `docs/display-output.md` lines 753-755 and 1191-1193 do.
DISPLAY_2026_09_21 = [
    ("""               and against DVI 1.0, and a monitor on the HDMI TX connector
               shows the machine's own screen as built --- 1280 by 1024 with
               the CADR's 768 by 963 centered in it, white on black. The port""",
     """               and against DVI 1.0, and a monitor on the HDMI TX connector
               shows the machine's own screen, 768 by 963, white on black, in
               a 1280 by 1024 raster. The first display sits at the raster's
               left edge and the color board at its right; that monitor
               reading was taken on a build that centered the first display,
               before it was moved. The port"""),
    ('<text class="d-s" x="-70" y="346" text-anchor="middle">centered, the color one over</text>\n'
     '          <text class="d-s" x="-70" y="360" text-anchor="middle">the first; TMDS out to HDMI</text>',
     '<text class="d-s" x="-70" y="346" text-anchor="middle">side by side, the color one</text>\n'
     '          <text class="d-s" x="-70" y="360" text-anchor="middle">over the first; TMDS to HDMI</text>'),
    ('<text class="d-s" x="-233" y="358" text-anchor="middle">one of three modes</text>',
     '<text class="d-s" x="-233" y="358" text-anchor="middle">1280 &times; 1024, 60 Hz</text>'),
    ('the monochrome one, the color one, or both, each centered on the raster at 1:1 with the rest black '
     'and the color screen drawn over the monochrome one where they overlap.',
     'the monochrome one, the color one, or both, at 1:1 with the rest black and neither of them scaled. '
     "The monochrome screen sits at the raster's left edge and the color one at its right, "
     'so the two share the sixty-four columns in the middle that 1280 is too narrow to give them separately, '
     'and in those columns the color screen is drawn over the monochrome one.'),
    ('so the block reads a word column at a time and the picture is still read exactly once a frame.',
     'so the block reads a word column at a time and the picture is still read exactly once a frame; '
     'turned, the widths are the heights, so the two screens share a hundred and thirty-seven columns there instead of sixty-four.'),
    ('The video mode is not a setting but a build: a mode is a pixel clock, a pixel clock comes from a clock '
     'generator whose dividers are fixed in the bitstream, and the three modes want three different clock '
     'frequencies, so three bitstreams carry the three modes --- 1280 by 1024 at 60 hertz, 1400 by 1050 at 60 '
     'with reduced blanking, and 1920 by 1080 at 30 --- and the console reports which one the fabric is.',
     'There is one video mode and the bitstream fixes it: ' + F.display('arty-z7-20') + ' at 60 hertz, on a pixel clock of 108 '
     'megahertz. A mode is a pixel clock, and a pixel clock comes from a clock generator whose dividers the '
     'bitstream sets, so another mode would be another bitstream rather than a setting. It is a 5:4 mode, and '
     'a display that will not take 5:4 will not take this output.'),
    ("and a monitor on that connector shows the machine's own screen as built, over the port drawn beneath it.",
     "and a monitor on that connector shows the machine's own screen, over the port drawn beneath it; "
     "that reading was taken on a build that centered the first display, before it was moved to the raster's left edge."),
]
ARTY_FIT += DISPLAY_2026_09_21

# THE NOTE BESIDE THE BOARD TABLE.  `front.css` asks for it in as many words:
# why a cell says what it says is on the cell as a title AND in the note
# beside the table, because a title alone is a fact only a pointer can read.
# What a cell cannot carry goes in this note, in sentences, rather than into a
# mark nobody follows.
BOARDS_NOTE = ('Every board has Ethernet and a microSD card, so the table leaves them out. '
               'A bar is the share of the chip&rsquo;s logic and block memory that a machine uses; under QUUX&rsquo;s, the period of its clock and its cache on that board.')

# THE BOARDS' TABLE, one row a board, written here from data and not lifted.
# THE FIGURES are each board's own place and route report for the fabric it
# runs, in that part's own terms, and they are gen/facts.py's: the CADR's
# fits are the ones its released cards are built from, and QUUX's are its
# design's.  The Kria KR260's QUUX block memory is block RAM tiles and
# UltraRAM both, so its cell has a third bar.  A bar is the percentage of the
# part used, and the percentage is the figure that compares across the rows:
# lookup tables and block RAM tiles on the Zynq boards, ALMs and M20K blocks on
# the DE25-Nano, which are different units (Altera's own conversion guide puts
# one ALM at about 1.3 lookup tables, section 2.2, "AMD vs Altera FPGA
# Resource", of "Design Conversion Guidelines: AMD Zynq 7000 SoC and
# Ultrascale+ MPSoC to Agilex 5 FPGAs and SoCs", Altera document 826363,
# revision 2026-01-27).  Memory built out of logic is counted inside the
# logic figure and never reported beside it.  Under QUUX's bars, the period
# of its clock and its cache on that board.
# A CELL HAS THREE READINGS AND NOT TWO: yes where that board itself has run
# the thing, yes with a qualification where the thing is built into that board
# and nothing of it has run there yet, and no where the board does not have
# the thing at all.  The middle one is a footnote in the cell and not a third
# grade, because the five-step status vocabulary this site retired is what it
# must not grow back into.  It is not the drawings' green, which says a block
# is this project's work and built and checked, not that it has run.
def _fit_row(board, machine):
    f = F.fit(board, machine)
    unit = {'BRAM': 'block RAM tiles', 'M20K': 'M20K blocks'}[f.memory_unit]
    return (machine.upper(), f.logic, f.logic_total, f.logic_unit, f.memory, f.memory_total, unit) + \
        ((f.uram + ('UltraRAM blocks',),) if f.uram else ())

def _display_cell(board):
    return ('text', '', '%s|%s|60 Hz' % (F.DISPLAY[board][0], F.display(board, '&times;')))

BOARD_ROWS = [
    # (file, name, product, part, maker, maker's page, machines, cpu,
    #  [(machine, logic used, logic total, logic unit, memory used, memory total, memory unit[, (more used, more total, more unit)])],
    #  display, USB input) -- each cell is (word, title, footnote)
    ('arty-z7-20.html', 'Arty Z7-20', 'AMD Zynq 7020', 'XC7Z020', 'Digilent', DIGILENT_ARTY, 'CADR, QUUX', '2 x Arm Cortex-A9, Linux',
     [_fit_row('arty-z7-20', 'cadr'), _fit_row('arty-z7-20', 'quux')],
     [_display_cell('arty-z7-20'), ('text', '', 'Keyboard<br>Mouse')]),
    ('kria-kr260.html', 'Kria KR260', 'AMD Zynq UltraScale+ K26', 'XCK26', 'AMD', AMD_KR260, 'CADR, QUUX', '4 x Arm Cortex-A53, Linux',
     [_fit_row('kria-kr260', 'cadr'), _fit_row('kria-kr260', 'quux')],
     [_display_cell('kria-kr260'), ('text', '', 'Keyboard<br>Mouse')]),
    ('de25-nano.html', 'DE25-Nano', 'Altera Agilex 5 E-series', 'A5EB013B', 'Terasic', TERASIC_DE25, 'CADR, QUUX', '2 x Arm Cortex-A76 and 2 x Cortex-A55, Linux',
     [_fit_row('de25-nano', 'cadr'), _fit_row('de25-nano', 'quux')],
     [_display_cell('de25-nano'), ('text', '', 'Keyboard<br>Mouse')]),
]

def resource_bars(rows):
    """A bar for each machine: the share of the part used, its percentage inside
    the outline, in the filled part where there is room (40% and over) and just
    after the fill where there is not, and the figures in small text under it."""
    out = ''
    for machine, used, total, unit in rows:
        pct = round(100.0 * used / total, 1)
        place = ('right:calc(100%% - %s%%)' % num(pct)) if pct >= 40 else ('left:calc(%s%% + 3px)' % num(pct))
        out += ('<div class="rb"><span class="rb-m">%s</span><span class="rb-wrap"><span class="rb-bar"><i style="width:%s%%"></i>'
                '<b style="%s">%.1f%%</b></span><span class="pc">%s / %s %s</span></span></div>'
                % (machine, num(pct), place, pct, format(used, ','), format(total, ','), unit))
    return out


def board_table():
    head = ('<thead>\n          <tr>\n            <th scope="col" class="board">Board</th>\n'
            '            <th scope="col">CADR</th>\n            <th scope="col">QUUX</th>\n'
            '            <th scope="col">Display</th>\n'
            '            <th scope="col">USB input</th>\n          </tr>\n        </thead>\n')
    body = ''
    for fname, name, product, part, maker, url, machines, cpu, fits, cells in BOARD_ROWS:
        body += '          <tr>\n'
        body += ('            <th scope="row" class="board"><a href="%s">%s</a><span class="pc">%s</span><span class="pc">%s</span>'
                 '<span class="pc">made by <a href="%s">%s</a></span></th>\n' % (fname, name, product, part, url, maker))
        for machine in ('CADR', 'QUUX'):
            mine = [f for f in fits if f[0] == machine]
            if mine:
                _, lu, lt, lun, mu, mt, mun = mine[0][:7]
                bars = resource_bars([(lun, lu, lt, lun),
                                      ('BRAM' if 'RAM' in mun else mun.split()[0], mu, mt, mun)]
                                     + [('URAM', xu, xt, xun) for xu, xt, xun in mine[0][7:]])
                if machine == 'QUUX':
                    b = fname[:-len('.html')]
                    bars += ('<span class="pc">%s&nbsp;MHz (%s&nbsp;ns clock)</span>'
                             '<span class="pc">%s words cache</span>'
                             % (F.mhz(b), F.period(b), F.cache_k(b)))
                body += '            <td class="num rbs">%s</td>\n' % bars
                continue
            body += '            <td class="st no">not supported</td>\n'
        for word, title, foot in cells:
            if word == 'text':      # a connector's name, and not a yes or a no
                label, *lines = foot.split('|')
                body += ('            <td class="st plain"%s>%s%s</td>\n'
                         % (' title="%s"' % title if title else '', label, ''.join('<span class="pc">%s</span>' % l for l in lines)))
                continue
            body += ('            <td class="st%s"%s>%s%s</td>\n'
                     % ('', ' title="%s"' % title if title else '', word,
                        '<span class="pc">%s</span>' % foot if foot else ''))
        body += '          </tr>\n'
    return ('    <div class="table-scroll" tabindex="0" role="region" aria-label="What each board is and what it runs">\n'
            '      <table class="boardtable">\n        ' + head + '        <tbody>\n' + body + '        </tbody>\n      </table>\n    </div>\n')


# ---------------------------------------------------------------- the chrome

# The characters and the Cold Boot chrome these pages were drawn with are gone:
# the site's head, header and footer are gen/chrome.py's, and a page here is
# what goes inside <main>.  Each section is a `section wrap` with the site's
# eyebrow and heading; a figure carries a "FIG." line over the drawing.

WRITTEN = []

# THE SITE'S TERMS, over the words lifted from muir-fpga's pages and
# documents: the simulator is muir-sim, where muir-fpga still says muir (bare
# muir is the whole project); and the machine is a Lisp Machine.  Only what a reader sees or hears is renamed: HTML comments are left
# as they are, and so is every file name such as muir.commit and every
# address such as muir-fpga's.
def site_terms(html):
    def terms(s):
        s = re.sub(r'\bmuir\b(?![-.]\w)', 'muir-sim', s)
        return re.sub(r'\bLisp machine', 'Lisp Machine', s)
    parts = re.split(r'(<!--.*?-->)', html, flags=re.S)
    return ''.join(p if p.startswith('<!--') else terms(p) for p in parts)

# LABELS THAT DO NOT FIT THEIR BOX IN PLEX MONO, and that fit.py could not set
# again without leaving the box: the words the drawing says instead, each
# taken out of the words it said and nothing added.  A label is written as
# the page has it after site_terms(), a page is named by the boards that carry
# the label, and a label that is not there stops the run.
A, D = 'arty-z7-20.html', 'de25-nano.html'
K = 'kria-kr260.html'
def _t(cls, x, y, anchor, words):
    return '<text class="%s" x="%s" y="%s"%s>%s</text>' % (cls, x, y, ' text-anchor="middle"' if anchor else '', words)
LABELS = [
    ((A, D, K), '>for the other machines<', '>for other machines<'),
    ((A, D, K), '>the console and JTAG<', '>console and JTAG<'),
    ((A, K), '>one micro-USB socket,<', '>micro-USB socket,<'),
    ((A,), '>PL masters, 64 bits, AXI3<', '>FPGA masters, 64-bit<'),
    ((A,), _t('d-s', 1162, 460, 1, 'PS masters, 32 bits, AXI3'), _t('d-s', 1162, 460, 1, 'Arm masters, 32-bit')),
    ((A,), '>PS masters, 32 bits, AXI3<', '>Arm masters, 32 bits, AXI3<'),
    ((A, K), '>on the PS,<', '>on Linux,<'),
    ((A, D, K), '>the control store: 16K &times; 48, 768 Kb<', '>control store: 16K &times; 48, 768 Kb<'),
    ((A, D, K), '>the debugger<', '>debugger<'),
    ((A, D, K), '>Vcc open at both sides<', '>Vcc open both sides<'),
    ((A, D), '>U-Boot, the CADR&rsquo;s bitstream,<', '>U-Boot, CADR bitstream,<'),
    ((A, D, K), '>Linux and its root filesystem,<', '>Linux, root filesystem,<'),
    ((A, D, K), '>and the disk packs, a file a drive<', '>disk packs, a file each<'),
    # the boxes of the lower row take three lines of a body and one of a name,
    # so a body that ran to four lines is written in three
    ((A, D, K), _t('d-s', 599, 586, 1, 'the CADR&rsquo;s serial line') + '\n          ' + _t('d-s', 599, 600, 1, 'on a TCP socket,') + '\n          '
     + _t('d-s', 599, 622, 1, 'as muir-sim offers it'),
     _t('d-s', 599, 586, 1, 'serial line on a') + '\n          ' + _t('d-s', 599, 600, 1, 'TCP socket, as') + '\n          '
     + _t('d-s', 599, 614, 1, 'muir-sim does')),
    ((A, D, K), _t('d-s', 746, 586, 1, 'a drive&rsquo;s blocks as a file,') + '\n          ' + _t('d-s', 746, 600, 1, 'one file a drive') + '\n          '
     + _t('d-s', 746, 622, 1, 'staged into DDR'),
     _t('d-s', 746, 586, 1, 'a drive is a file,') + '\n          ' + _t('d-s', 746, 600, 1, 'its blocks staged') + '\n          '
     + _t('d-s', 746, 614, 1, 'into DDR')),
    ((A,), _t('d-s', 893, 586, 1, 'halt, step and inspect') + '\n          ' + _t('d-s', 893, 600, 1, 'over M_AXI_GP1') + '\n          '
     + _t('d-s', 893, 622, 1, 'a Unibus master'),
     _t('d-s', 893, 586, 1, 'halt, step and') + '\n          ' + _t('d-s', 893, 600, 1, 'inspect over') + '\n          '
     + _t('d-s', 893, 614, 1, 'M_AXI_GP1') + '\n          ' + _t('d-s', 893, 628, 1, 'a Unibus master')),
    ((D,), _t('d-s', 893, 586, 1, 'halt, step and inspect') + '\n          ' + _t('d-s', 893, 600, 1, 'over LWH2F') + '\n          '
     + _t('d-s', 893, 622, 1, 'a Unibus master'),
     _t('d-s', 893, 586, 1, 'halt, step and') + '\n          ' + _t('d-s', 893, 600, 1, 'inspect over') + '\n          '
     + _t('d-s', 893, 614, 1, 'LWH2F') + '\n          ' + _t('d-s', 893, 628, 1, 'a Unibus master')),
    ((A, D, K), '>four registers, and the channel<', '>four registers, the channel<'),
    ((A, D, K), '>a second display board,<', '>second display board:<'),
    ((A, D, K), '>576 &times; 454, 4 bits a pixel<', '>576 &times; 454 &times; 4 bits<'),
    ((A, D, K), _t('d-s', 1040, 586, 1, 'the keyboard and mouse,') + '\n          ' + _t('d-s', 1040, 600, 1, 'onto the I/O board') + '\n          '
     + _t('d-s', 1040, 622, 1, 'through the terminal'),
     _t('d-s', 1040, 586, 1, 'the keyboard and') + '\n          ' + _t('d-s', 1040, 600, 1, 'mouse, onto the') + '\n          '
     + _t('d-s', 1040, 614, 1, 'I/O board') + '\n          ' + _t('d-s', 1040, 628, 1, 'via the terminal')),
    ((D,), '>2 &times; Cortex-A76<', '>2&times;Cortex-A76<'),
    ((D,), '>2 &times; Cortex-A55<', '>2&times;Cortex-A55<'),
    ((A, D, K), '<text class="d-s" x="1066" y="228" text-anchor="end">Unibus, 16 bits, open collector</text>',
     '<text class="d-s" x="1066" y="214" text-anchor="end">Unibus, 16 bits,</text>\n          <text class="d-s" x="1066" y="228" text-anchor="end">open collector</text>'),
    ((K,), '>boot.scr, the CADR&rsquo;s bitstream,<', '>boot.scr, bitstream,<'),
    ((K,), _t('d-s', 893, 586, 1, 'halt, step and inspect') + '\n          ' + _t('d-s', 893, 600, 1, 'over HPM1') + '\n          '
     + _t('d-s', 893, 622, 1, 'a Unibus master'),
     _t('d-s', 893, 586, 1, 'halt, step and') + '\n          ' + _t('d-s', 893, 600, 1, 'inspect over') + '\n          '
     + _t('d-s', 893, 614, 1, 'HPM1') + '\n          ' + _t('d-s', 893, 628, 1, 'a Unibus master')),
    # the HDMI box is 100 wide and takes 14 letters a line, so its four lines
    # start one line higher than the three they replace
] + [((page,), _t('d-s', -233, 330, 1, 'the display,') + '\n          ' + _t('d-s', -233, 344, 1, 'from the fabric,') + '\n          '
       + _t('d-s', -233, 358, 1, '1280 &times; 1024, 60 Hz'),
       _t('d-s', -233, 326, 1, 'display out of') + '\n          ' + _t('d-s', -233, 340, 1, 'the fabric,') + '\n          '
       + _t('d-s', -233, 354, 1, F.display(page[:-len('.html')], ' &times; ')) + '\n          ' + _t('d-s', -233, 368, 1, 'at 60 Hz'))
      for page in (A, D)]

DEBUGGING = ('debugging.html',)
LABELS += [
    # the header's box is 22 wide and four letters of the 9.5-unit label are 22.8
    (DEBUGGING, '<text class="d-x" x="21.0" y="406.0" text-anchor="middle">MIPI</text>',
     '<text class="d-x" x="21.0" y="406.0" text-anchor="middle" style="font-size:8.5px">MIPI</text>'),
]
BOOTING = ('booting.html',)
LABELS += [
    # the sequences' title is 7.8 units a letter now, so its subtitle starts a
    # gap of 30 after it
    (BOOTING, '<text class="d-s" x="225" y="18">everything from', '<text class="d-s" x="297" y="18">everything from'),
    (BOOTING, '<text class="d-s" x="256" y="18">the microSD card holds', '<text class="d-s" x="290" y="18">the microSD card holds'),
    (BOOTING, '<text class="d-s" x="240" y="18">the flash carries', '<text class="d-s" x="305" y="18">the flash carries'),
    (BOOTING, '<text class="d-s" x="245" y="18">the flash and the card carry', '<text class="d-s" x="297" y="18">the flash and the card carry'),
    # the sequences' labels that ran across a lifeline, said in the room between
    (BOOTING, '<text class="d-s" x="337" y="100" text-anchor="middle">the first phase', '<text class="d-s" x="220" y="100">the first phase'),
    (BOOTING, '<text class="d-s" x="307" y="100" text-anchor="middle">the first phase', '<text class="d-s" x="220" y="100">the first phase'),
    (BOOTING, '>S80: the card mounted read-write, the clock back from the bay</text>\n          <line class="d-line" x1="635" y1="568"',
     '>S80: the card mounted read-write, clock back from the bay</text>\n          <line class="d-line" x1="635" y1="568"'),
    (BOOTING, '<text class="d-s" x="377" y="686" text-anchor="middle">S80: the card mounted read-write, the clock back from the bay</text>',
     '<text class="d-s" x="377" y="672" text-anchor="middle">S80: the card mounted read-write,</text>\n          <text class="d-s" x="377" y="686" text-anchor="middle">the clock back from the bay</text>'),
    (BOOTING, '>uEnv.txt again &mdash; the card&rsquo;s server, not the lease&rsquo;s<', '>uEnv.txt again: the card&rsquo;s server, not the lease&rsquo;s<'),
    (BOOTING, '<text class="d-s" x="583" y="818">login on the serial console</text>', '<text class="d-s" x="583" y="818">serial console login</text>'),
    (BOOTING, '<text class="d-s" x="413" y="706">384 MB &mdash; 0x18000000 and up is the CADR&rsquo;s</text>', '<text class="d-s" x="413" y="706">Linux %s kB; the CADR&rsquo;s from 0x1B000000</text>' % F.num(F.LINUX_CADR_KB['arty-z7-20'])),
    # THE CADR'S RESERVATION IS 17.125 MB, at 0x1B000000 on the Zynq boards and 0xB3000000 on the DE25-Nano
    # (rtl/plumbing/cadr_ddr_map.sv, docs/linux.md of muir-fpga), and Linux has the rest (gen/facts.py).
    (BOOTING, '<text class="d-s" x="578" y="596">384 MB &mdash; 0x18000000 and up is the CADR&rsquo;s</text>',
     '<text class="d-s" x="578" y="596">Linux %s kB &mdash; 0x1B000000 to 0x1C11FFFF is the CADR&rsquo;s</text>' % F.num(F.LINUX_CADR_KB['arty-z7-20'])),
    (BOOTING, 'the CADR&rsquo;s 128 MB reserved</text>', 'the CADR&rsquo;s 17.125 MB reserved</text>'),
    (BOOTING, '128 MB reserved at 0xB0000000</text>', '17.125 MB reserved at 0xB3000000</text>'),
    (BOOTING, '&mdash; 128 MB reserved</text>', '&mdash; 17.125 MB reserved</text>'),
    (BOOTING, '1 GiB &mdash; 0xB0000000 to 0xB7FFFFFF is the CADR&rsquo;s</text>', 'Linux %s kB &mdash; 0xB3000000 to 0xB411FFFF is the CADR&rsquo;s</text>' % F.num(F.LINUX_CADR_KB['de25-nano'])),
    (BOOTING, "with the CADR's 128 MB kept from it.", "with the CADR's 17.125 MB kept from it."),
    (BOOTING, "with the CADR's 128 MB reserved at 0xB0000000.", "with the CADR's 17.125 MB reserved at 0xB3000000."),
    (BOOTING, "with the CADR's 128 MB reserved, and the boot", "with the CADR's 17.125 MB reserved, and the boot"),
    # the Zynq-7000 boards start ozd too (S84), as the DE25-Nano does
    (BOOTING, '<text class="d-s" x="578" y="536">S85 the screen over RFB, S86 the serial line, S87 Chaosnet,</text>\n          <text class="d-s" x="578" y="552">S88 a USB keyboard and mouse &mdash; a board with no USB host leaves it out</text>',
     '<text class="d-s" x="578" y="536">S84 ozd, S85 the screen over RFB, S86 the serial line,</text>\n          <text class="d-s" x="578" y="552">S87 Chaosnet, S88 a USB keyboard and mouse where there is a USB host</text>'),
    (BOOTING, '<text class="d-s" x="413" y="646">S85 the screen over RFB, S86 the serial line, S87 Chaosnet,</text>\n          <text class="d-s" x="413" y="662">S88 a USB keyboard and mouse &mdash; a board with no USB host leaves it out</text>',
     '<text class="d-s" x="413" y="646">S84 ozd, S85 the screen over RFB, S86 the serial line,</text>\n          <text class="d-s" x="413" y="662">S87 Chaosnet, S88 a USB keyboard and mouse where there is a USB host</text>'),
    # a note that ran on to the right of the drawing goes under the one beside it
    (BOOTING, '<text class="d-s" x="560" y="884" fill-opacity="0.62">the times down', '<text class="d-s" x="10" y="898" fill-opacity="0.62">the times down'),
]

def fix_labels(text, fname):
    for pages, old, new in LABELS:
        if fname in pages:
            assert old in text, (fname, old)
            text = text.replace(old, new)
    return text

def page(fname, title, desc, parts, css=()):
    main = fit.fit_labels(fix_labels(site_terms(''.join(parts)), fname), fname)
    desc = site_terms(desc)
    html = chrome.page('fpga/' + fname, title, desc, main, section='fpga',
                       css=('drawings.css',) + tuple(css))
    open(os.path.join(OUT, fname), 'w', encoding='utf-8').write(html)
    WRITTEN.append(fname)

def upper(html):
    """HTML in capitals: its text is upper-cased, its entities and tags are not
    (&rsquo; upper-cased is &RSQUO;, which is no entity)."""
    return ''.join(p if i % 2 else p.upper()
                   for i, p in enumerate(re.split(r'(&#?[A-Za-z0-9]+;|<[^>]*>)', html)))

def hero(eyebrow, title, lede, body='', keys='', side='', cls=''):
    """The top of a page: its eyebrow, its title, its lede and anything
    under it, and the keys to the pages it leads to."""
    return ('<section class="page-hero wrap%s">\n<div>\n'
            '<p class="eyebrow"><span class="dot"></span>%s</p>\n<h1>%s</h1>\n'
            '<p class="intro">%s</p>\n%s%s</div>\n%s</section>\n'
            % (('' if side else ' solo') + (' ' + cls if cls else ''), eyebrow, title, lede, body, keys, side))

def keys(*ks, first='key'):
    """The keys to other pages, as the design's links: a button for the
    first where `first` is 'key', and text links for the rest."""
    out = '<div class="actions">'
    for i, (href, text) in enumerate(ks):
        out += '<a class="%s" href="%s">%s</a>' % ('button' if first == 'key' and i == 0 else 'text-link', href, text)
    return out + '</div>\n'

def section(sid, eyebrow, title, lead, body, label=None):
    """A section of a page: its eyebrow and heading, a sentence or two under
    them, and what it holds."""
    return ('<section%s class="section wrap" aria-label="%s">\n'
            '<div class="section-heading"><div><p class="eyebrow">%s</p><h2>%s</h2></div></div>\n%s%s</section>\n'
            % (' id="%s"' % sid if sid else '', label or re.sub(r'<[^>]+>', '', title.replace('<br>', ' ')), eyebrow, title,
               '<p class="lead">%s</p>\n' % lead if lead else '', body))

def figure(svg, caption, cls='fig', more='', label='', name=''):
    """A drawing in its box, which scrolls sideways where the drawing is
    wider than the screen; the box can be reached from the keyboard and is
    named after the figure: `name` is its title as written, `label` the
    figure's number and title above it."""
    n = int(re.match(r'FIG\. (\d+)', label).group(1))
    return ('<figure class="%s">\n<div class="fig-top"><span>%s</span><span>MUIR-FPGA</span></div>\n'
            '<div class="scroll" tabindex="0" role="region" aria-label="Figure %d: %s">\n        %s\n</div>\n<figcaption>%s</figcaption>\n%s</figure>\n'
            % (cls, label, n, name, svg, caption, more))



# ================================================================ front page

# The herald is a crop of rows 1 to 140 and columns 1 to 638 of the Kria KR260's screen
# after a cold boot of QUUX with System 2001 (1920 x 1080, white on black), unscaled.
HERALD = '''<figure class="fig herald">
<div class="fig-top"><span>QUUX ON THE KRIA KR260</span><span>MUIR-FPGA</span></div>
<img src="kr260-herald.png" width="638" height="140" alt="QUUX&rsquo;s screen on the Kria KR260 after a cold boot: [Loading error table for microcode version 2001]; MIT System, band 1 of LISPM-1.; 32768K physical memory, 131072K virtual memory.; Experimental System 2001; Microcode 2001; Machine Type QUUX on Kria KR260; MIT Lisp Machine One, with associated machine HOST.; ;Reading at top level in Lisp Listener 1.; ;Reading in base 10 in package USER with standard traditional syntax readtable.">
<figcaption>QUUX&rsquo;s herald on the Kria KR260 after a cold boot, cut from its screen.</figcaption>
</figure>
'''

def build_index():
    table = board_table()
    P = []
    P.append(hero('muir-fpga &middot; QUUX and the CADR in FPGA fabric', 'QUUX and the CADR,<br>in <em>FPGA fabric.</em>',
                  'What runs on each of the boards.',
                  body='<p class="hero-description">Every part of it is held to <a href="../simulator/">muir-sim</a>, a simulator of the same machines, tick for tick. The CADR runs within about 5% of MIT&rsquo;s speed (<a href="faq.html">why</a>). QUUX runs as a pipeline of four stages, a clock a stage, at the period each board&rsquo;s fit closes at, which <a href="#boards">the boards&rsquo; table</a> gives.</p>\n',
                  keys=keys(('#boards', 'The boards'), ('#using', 'Using it'), ('../cadr/', 'CADR'), ('../quux/', 'QUUX'))
                       + HERALD, cls='has-herald'))

    # The two speech bubbles this section had are plain sentences now, in
    # the same words.
    P.append(section('what', '01 / WHAT IT IS', 'QUUX and the CADR<br>in the <em>fabric.</em>', '', '''<div class="cols">
<div class="prose">
<p>muir-fpga puts QUUX and the CADR in the fabric of an FPGA. The CADR is the Lisp Machine MIT designed around 1978, and muir-fpga&rsquo;s CADR is <a href="../simulator/">muir-sim</a>&rsquo;s RTL model of it, synthesized into the fabric of an FPGA &mdash; the two processor boards, the bus interface, the disk controller, the display and the I/O board.</p>
</div>
<div class="prose">
<p>The same fabric is built as QUUX too, the CADR evolved; <a href="#boards">the boards&rsquo; table</a> says which board runs which. Each machine boots its own <a href="../system/">muir-sys</a> system, and the CADR gets its files and the time from <a href="../ozd/">ozd</a>.</p>
<div class="actions"><a class="text-link" href="arty-z7-20.html">Arty Z7-20</a><a class="text-link" href="kria-kr260.html">Kria KR260</a><a class="text-link" href="de25-nano.html">DE25-Nano</a></div>
</div>
</div>
'''))

    P.append(section('boards', '02 / THE BOARDS', 'The boards,<br>and what <em>each runs.</em>', BOARDS_NOTE, table))

    # USING IT: the files and the card, from the release notes of muir-fpga's
    # `latest` release and muir-sys's `latest-cadr` and `latest-quux`.
    FZ = 'https://github.com/metebalci/muir-fpga/releases/download/latest/'
    SZ = 'https://github.com/metebalci/muir-sys/releases/download/'
    def zip_cell(machine, board):
        name = '%s-%s.zip' % (machine, board)
        return '<td><a href="%s%s"><code>%s</code></a></td>' % (FZ, name, name)
    zrows = ''
    for board, slug in (('Arty Z7-20', 'arty-z7-20'), ('Kria KR260', 'kria-kr260'), ('DE25-Nano', 'de25-nano')):
        zrows += '<tr><th scope="row" class="board">%s</th>%s%s</tr>\n' % (
            board, zip_cell('cadr', slug), zip_cell('quux', slug))
    zips = ('<div class="table-scroll" tabindex="0" role="region" aria-label="The zip for each board and machine"><table>\n'
            '<thead><tr><th scope="col" class="board">Board</th><th scope="col">CADR</th><th scope="col">QUUX</th></tr></thead>\n'
            '<tbody>\n%s</tbody>\n</table></div>\n' % zrows)
    systems = '''<div class="cols">
<div class="prose">
<p><b>The CADR</b>, from <a href="https://github.com/metebalci/muir-sys/releases/tag/latest-cadr">muir-sys&rsquo;s latest-cadr</a>:</p>
<ul>
<li><a href="%(s)slatest-cadr/cadr-pack.img.gz"><code>cadr-pack.img.gz</code></a>, uncompressed and copied to the card as <code>packs/disk-pack-0.img</code>.</li>
<li><a href="%(s)slatest-cadr/cadr-sys.tar.gz"><code>cadr-sys.tar.gz</code></a>, unpacked; its <code>sys</code> and <code>site</code> folders go onto the card&rsquo;s <code>sys/</code> and <code>site/</code>.</li>
</ul>
</div>
<div class="prose">
<p><b>QUUX</b>, from <a href="https://github.com/metebalci/muir-sys/releases/tag/latest-quux">muir-sys&rsquo;s latest-quux</a>:</p>
<ul>
<li><a href="%(s)slatest-quux/quux-disk.vhd.gz"><code>quux-disk.vhd.gz</code></a>, uncompressed and copied to the card as <code>packs/disk-pack-0.img</code>.</li>
<li><a href="%(s)slatest-quux/quux-sys.tar.gz"><code>quux-sys.tar.gz</code></a>, unpacked; its <code>sys</code> and <code>site</code> folders go onto the card&rsquo;s <code>sys/</code> and <code>site/</code>.</li>
</ul>
</div>
</div>
''' % {'s': SZ}
    steps = [
        ('Format a microSD card.', 'One FAT32 partition with an MBR partition table, not exFAT, which cards over 32&nbsp;GB get by default. Any volume name will do.'),
        ('Unzip the zip onto it.', 'Your board&rsquo;s zip, onto the root of the card. A zip works only on the board it is named for.'),
        ('Add the system.', 'The disk as <code>packs/disk-pack-0.img</code>, and the <code>sys</code> and <code>site</code> folders as <code>sys/</code> and <code>site/</code>, from the downloads above. The <code>README.TXT</code> in each zip names the System its card is for, with the muir-sys release and the files. Both boot with an empty <code>sys/</code>, on the band&rsquo;s own error table; loading or compiling a file of the system needs its <code>sys</code> and <code>site</code> folders on the card. The machine reads and writes <code>sys/</code> and <code>site/</code>, so a file it compiles is written beside its source, and a tree it damages is put back from the system&rsquo;s sources tarball.'),
        ('Set the date.', 'The boards keep no time while switched off. With a network, a board sets its clock by NTP at boot, from <code>pool.ntp.org</code>, before the machine starts; <code>--ntp-server</code> in <code>fpgarc</code> names another server and <code>--no-ntp</code> turns it off. Without a network, open <code>fpgarc</code> on the card and replace the two lines <code>#--date yyyyMMdd</code> and <code>#--time HHmm</code> with today&rsquo;s date and the time in UTC, for example <code>--date 20261002</code> and <code>--time 1430</code>. With neither, the machine starts in 1970.'),
        ('Connect a screen and input.', 'A monitor and a USB keyboard and mouse (HDMI on the Arty Z7-20 and the DE25-Nano, DisplayPort, J6, on the Kria KR260), or Ethernet to a network with DHCP and a VNC viewer on port 5900 of the board&rsquo;s address. On the Kria KR260 the network port is J10C, and its USB ports are for the keyboard and the mouse, with no other USB storage plugged in. On the Arty Z7-20 and the DE25-Nano the address can change from one boot to the next, so look for it in your router&rsquo;s list.'),
        ('Switch the board on.', 'Linux starts, and the machine boots from its disk by itself in about two minutes. The first time the machine reads a file it asks you to log in: log in as <code>lispm</code>, the name whose home directory the card provides.'),
    ]
    stepsh = '<div class="steps-list">\n' + ''.join(
        '<article class="step"><div class="step-heading"><span class="step-number">%02d</span><h3>%s</h3></div><p>%s</p></article>\n' % (i + 1, h, t)
        for i, (h, t) in enumerate(steps)) + '</div>\n'
    P.append(section('using', '03 / USING IT', 'From a card<br>to a <em>prompt.</em>',
                     'Ready-made files for a microSD card, a zip for each board and machine. Nothing has to be built.',
                     zips + systems + stepsh +
                     '<p class="small-print">The CADR&rsquo;s card makes it LISPM-1, at Chaosnet address 177201; <a href="../system/releases.html#running">the release notes</a> give its site&rsquo;s other machines. '
                     'The CADR has 32 memory boards by default; <code>--main-memory-boards</code> in <code>fpgarc</code> says another count from 1 to 60, and System 1003 and later use more; an older system halts at its cold boot with more than 32. '
                     + 'On a QUUX card, main memory is %dMW by default; <code>--main-memory-size</code> in <code>fpgarc</code> says another amount in MW, from 1MW to the board&rsquo;s most: %s. '
                     % (F.CARD_MEMORY_DEFAULT, ', '.join('%dMW on the %s' % (F.CARD_MEMORY_MOST[b], F.NAME[b]) for b in ('arty-z7-20', 'kria-kr260', 'de25-nano'))) +
                     'The <a href="https://github.com/metebalci/muir-fpga/releases/tag/latest">release page</a> lists the digests of the zips, and each of muir-sys&rsquo;s releases has a <code>SHA256SUMS</code> beside its files.</p>\n',
                     label='Using it'))


    # THE LICENSE TABLE FOLLOWS docs/license.md, which is its long form and
    # its source: the work in the repository no longer includes pages, and
    # the fonts are the site's, not muir-fpga's, so their row is gone.
    rows = [
        ('The work in this repository: the fabric, the checks and their reference traces, the programs beside the machine and the documents',
         'This project&rsquo;s. <b>GNU Affero General Public License, version 3 or later</b>',
         '<code>LICENSE</code>, and the SPDX identifier <code>AGPL-3.0-or-later</code> in almost every file&rsquo;s header'),
        ('Four files, for the Arty Z7-20: <code>ps7_init_gpl.c</code>, U-Boot&rsquo;s default environment, the board&rsquo;s device tree and the <code>-u-boot.dtsi</code> beside it',
         'This project&rsquo;s, under the <b>GNU General Public License, version 2 or later</b>, because each is compiled into U-Boot',
         'each file&rsquo;s own header'),
        ('Digilent&rsquo;s pin files',
         'Digilent&rsquo;s, under the <b>MIT License</b>',
         'the Arty Z7-20&rsquo;s constraint file cites the commit and digest of its pins'),
        ('<a href="../simulator/">muir-sim</a>',
         'Its own repository, under the <b>AGPL, version 3 or later</b>',
         'not carried; pinned by commit in <code>muir.commit</code>'),
        ('Buildroot 2026.02.3, U-Boot 2026.01, Linux 6.19.14',
         'Each under its own license; for the loader and the kernel, the <b>GPL, version 2</b>',
         'not in the repository; the build fetches them'),
        ('MIT&rsquo;s own files: the schematics, wire lists, print sets and PROM images of 1977 to 1981, and the system software beside them',
         'MIT&rsquo;s. No statement of terms came with the engineering files and none is made up for them; the system release states the <b>AGPL, version 3 or later</b>',
         'not in the repository; muir-sim carries them, recovered from the ITS backup tapes and unmodified'),
    ]
    trs = ''.join('<tr><th scope="row">%s</th><td>%s</td><td>%s</td></tr>\n' % r for r in rows)
    P.append(section('license', '04 / WHOSE WORK, UNDER WHAT TERMS', 'License and<br>third-party <em>material.</em>',
                     '',
                     '''<div class="table-scroll" tabindex="0" role="region" aria-label="License and third-party material"><table class="terms">
<thead><tr><th scope="col">What</th><th scope="col">Whose, and the terms</th><th scope="col">Where the terms are recorded</th></tr></thead>
<tbody>
%s</tbody>
</table></div>
''' % trs, label='License and third-party material'))

    P.append(section('colophon', '05 / ABOUT', 'MIT&rsquo;s machine, and<br>what muir-fpga <em>adds.</em>', '', '''<div class="prose">
<p>The CADR, the schematics, the wire lists and the microcode are MIT&rsquo;s, recovered by other people&rsquo;s work over decades, and the machine in the fabric is held tick for tick to <a href="../simulator/">muir-sim</a>; the documents list every source the drawings were read from and what each one is. The fabric, its checks and their reference traces, the programs beside the machine on the board and the documents are this project&rsquo;s.</p>
<p>muir-fpga is written with <a href="https://claude.com/claude-code">Claude Code</a>, using Anthropic&rsquo;s Claude Opus, Claude Fable and Claude Sonnet. The machine is written in SystemVerilog, its testbenches in C++ for Verilator, the programs beside it on the board in C, and the generators of its reference traces in Rust.</p>
<p>muir-fpga is muir-sim&rsquo;s RTL model of the CADR and of QUUX, synthesized into the fabric of an FPGA and held to muir-sim tick for tick.</p>
<p><b>&copy; 2026 Mete Balci.</b> muir-fpga is <a href="https://www.gnu.org/licenses/agpl-3.0.html">AGPL-3.0-or-later</a>. MIT&rsquo;s own files are not in this repository: muir-sim carries them, unmodified.</p>
</div>
''', label='About'))
    page('index.html', 'muir-fpga &mdash; the MIT CADR and QUUX in fabric',
         'The MIT CADR Lisp Machine and QUUX, the CADR evolved, in the fabric of small FPGA boards, held tick for tick to the muir-sim simulator: what runs on the Arty Z7-20, the Kria KR260 and the DE25-Nano.',
         P)

# ================================================================ board pages

# THE FRAME OF AN ARCHITECTURE DRAWING.  No outline is drawn around the board;
# the chip's own outline is the one labeled, with the FPGA's product name beside
# its part number, and the memory, the connectors, the lamps, the buttons and
# the Pmod headers stand outside it where they stood.  The key to the colors
# is one row under the drawing, centered on it.
#
# Nothing inside the drawing's <g> moves.  The viewBox is tightened to what the
# drawing itself occupies now that the outline is gone, and grown at the foot
# to hold the key.  Measured in Chromium with the page's own fonts, the <g>
# covers x 26 to 1766 and y 47 to 833 of the SVG's own units, strokes included;
# the viewBox keeps six units of paper on the left and the right of that, six
# over the chip's label, and five under the key, so the drawing's center is at
# x 896 and the key is centered there.
FRAME_VIEWBOX = '20 41 1813 829'
FRAME_CENTER = 926.5
KEY_SWATCH_Y = 851        # 18 units under the lowest box of the drawing
KEY_BASELINE = 861        # the words' baseline, 10 under the swatch's top as it was
KEY_TO_WORD = 7           # from a swatch's right edge to its word
KEY_GAP = 24              # from a word's end to the next swatch

# Each word's width is its letters times Plex Mono's advance, the face the
# drawing's `d-s` labels are set in at 11 units.  The advance is 600 units of
# 1,000 to the em at 400 and at 500, read in Chromium from the site's served
# ibm-plex-mono-400.woff2 and -500.woff2 at 1,000 pixels (a space, `M`, `i`,
# `W`, `x`, a digit, `.` and `%` each measured 600), so a word of n letters
# is n * 0.6 * 11 = 6.6n units, whole words included: `this project` measured
# 7,200 and `not available on this board` 16,200 at 1,000 pixels.
PLEX_ADVANCE = 0.6
KEY_FONT_SIZE = 11
KEY_WORDS = ('this project', 'another project', 'board component')
KEY_WIDTH = dict((w, round(len(w) * PLEX_ADVANCE * KEY_FONT_SIZE, 2)) for w in KEY_WORDS)

# WHOSE WORK EACH BLOCK IS, which is the whole of what the colors say.  Green
# is this project's and done, orange is another project's, carried here rather
# than built here, and gray is a part of the board itself.  A block of this
# project's that is not done yet carries no fill and has NO ENTRY HERE, because
# a block with no color reads as unfinished without being told.  What has been
# shown on silicon and what has only been built is no longer a distinction the
# drawing makes; docs/board.md makes it, session by session.
#
# The classes are the stylesheet's, and they still carry the names the old
# five-step axis gave them: `d-done` is the green, `d-part` the orange and
# `d-ext` the gray.  `d-built` and `d-wip` are now unused.
KEY_ITEMS = [('d-done', 'this project'), ('d-part', 'another project'),
             ('d-ext', 'board component')]

def num(v):
    return ('%.2f' % v).rstrip('0').rstrip('.')

def frame(svg, fname, part, product):
    items = KEY_ITEMS
    total = sum(13 + KEY_TO_WORD + KEY_WIDTH[w] for _, w in items) + KEY_GAP * (len(items) - 1)
    x = FRAME_CENTER - total / 2
    key = ['''          <!-- Whose work each block is: green this project's and done,
               orange another project's, carried here rather than built here,
               and gray a part of the board itself.  A block of this project's
               that is not done yet carries no fill and has no entry here,
               because a block with no color reads as unfinished without being
               told.  Nothing here says a block has been shown on silicon;
               docs/board.md says that, session by session.  The key is one row
               under the drawing, centered on it: every swatch and every word on
               one baseline, a swatch 7 units before its word and a word 24
               units before the next swatch, spaced by each word's own measured
               width. -->
''']
    for cls, word in items:
        key.append('          <rect class="d-box%s d-key" x="%s" y="%d" width="13" height="13"/>\n'
                   % (' ' + cls if cls else '', num(x), KEY_SWATCH_Y))
        key.append('          <text class="d-s" x="%s" y="%d">%s</text>\n' % (num(x + 13 + KEY_TO_WORD), KEY_BASELINE, word))
        x += 13 + KEY_TO_WORD + KEY_WIDTH[word] + KEY_GAP
    key.append('''          <!-- No outline around the board: the chip's outline below is the
               one that is drawn and labeled. -->
''')
    i = svg.index('          <!-- Whose work each block is')
    j = svg.index('          <g transform="translate(310,36)">')
    old = svg[i:j]
    assert old.count('<rect class="d-box" x="6" y="34" width="1841" height="819"/>') == 1, fname
    assert old.count('<text class="d-s" x="16" y="52">') == 1, fname
    svg = svg[:i] + ''.join(key) + svg[j:]
    svg = sub(svg, '<svg viewBox="0 0 1871 865"', '<svg viewBox="%s"' % FRAME_VIEWBOX)
    svg = sub(svg, '<text class="d-s" x="-164" y="24">%s</text>' % part,
              '<text class="d-s" x="-164" y="24">%s &middot; %s</text>' % (product, part))
    return svg

def board_svg(fname):
    svg = svgs(fname)[0]
    for o, n in {'arty-z7-20.html': ARTY_FIT}[fname]:
        svg = sub(svg, o, n)
    i, j = svg.index(FIT_FROM), svg.index(FIT_TO) + len(FIT_TO)
    svg = svg[:i] + cadr_fit_block(fname[:-len('.html')]) + svg[j:]
    return frame(svg, fname, *{'arty-z7-20.html': ('XC7Z020-1CLG400C', 'AMD Zynq 7020')}[fname])

# Every board page lists the other boards among its keys, in the site's order:
# the Arty Z7-20, the Kria KR260, the DE25-Nano.
BOARD_NAV = [('arty-z7-20.html', 'Arty Z7-20'),
             ('kria-kr260.html', 'Kria KR260'), ('de25-nano.html', 'DE25-Nano')]
BOARD_KEYS = dict((f, tuple(b for b in BOARD_NAV if b[0] != f)) for f, _ in BOARD_NAV)

# ozd AND muir ARE ORANGE, AND SO IS U-Boot.  All three are programs carried
# here rather than built here, and drawing them the way the memory and the
# controllers are drawn would say they arrived with the board.  They did not.
# The color is in the base drawings themselves, so nothing is substituted in
# here and the DE25-Nano's page inherits it with the rest of the Arty
# Z7-20's drawing.

# Each board page's eyebrow names its maker and its FPGA, so that no two board
# pages open on the same words.
BOARD_EYEBROW = {
    'arty-z7-20.html': 'muir-fpga &middot; Digilent &middot; Zynq 7020',
    'kria-kr260.html': 'muir-fpga &middot; AMD &middot; Zynq UltraScale+',
    'de25-nano.html': 'muir-fpga &middot; Terasic &middot; Agilex 5 E-series',
}

def build_board(fname, name, lede, corner_label, other, maker, body='', figlabel=None, quux=None):
    svg = board_svg(fname)
    title = re.search(r'<title>([^<]*)</title>', open(os.path.join(BASE, fname)).read()).group(1)
    board_page(fname, name, title, DESC[fname], lede, corner_label,
               (('booting.html', 'How it boots'), ('debugging.html', 'The debug cable')) + BOARD_KEYS[fname],
               maker, svg, body=body, figlabel=figlabel, quux=quux)

def board_page(fname, name, title, desc, lede, corner_label, key_list, maker, svg, body='', figlabel=None, quux=None, after='', own_keys=()):
    # The board's name, the one line naming its FPGA, the keys to the other
    # pages with the maker's own page last, and the drawing, which is the
    # whole point of the page.  A board that runs QUUX has a second drawing
    # after the CADR's, in the same style: "QUUX mapped onto" the board.  The
    # corner character is gone; corner_label is kept in the signature so that
    # the calls below read as they did.
    own = (('#cadr', 'The CADR&rsquo;s drawing'), ('#quux', 'QUUX&rsquo;s drawing')) if quux else ()
    own = own + tuple(own_keys)
    cores = [r[7] for r in BOARD_ROWS if r[0] == fname]
    if cores:
        body = '<p class="hero-description">The processing system: %s.</p>\n' % cores[0].replace(' x ', ' &times; ').replace(', Linux', ', running Linux') + body
    P = [hero(BOARD_EYEBROW[fname], name, lede, body=body,
              keys=keys(*(own + tuple(key_list) + ((maker, 'The maker&rsquo;s page &#8599;'),)), first='key lm')),
         '<section id="cadr" class="section wrap tight" aria-label="%s, the CADR&rsquo;s drawing">\n' % name,
         figure(svg, '', cls='fig dense wide', label='FIG. 01 &mdash; %s' % (figlabel or ((name.upper() + ', CADR') if quux else name.upper())), name=name).replace('<figcaption></figcaption>\n', ''),
         '</section>\n']
    if quux:
        P += ['<section id="quux" class="section wrap tight" aria-label="%s, QUUX&rsquo;s drawing">\n' % name,
              figure(quux, '', cls='fig dense wide', label='FIG. 02 &mdash; %s, QUUX' % name.upper(), name=name + ', QUUX').replace('<figcaption></figcaption>\n', ''),
              '</section>\n']
    P.append(after)
    page(fname, title, desc, P)

# THE DE25-NANO'S PAGE.  Its drawing is the Arty Z7-20's, generated from it
# with every block that is this project's work taking its color from
# DE25_STATUS below, and with no fill where that says the block is not done on
# this board.  What is drawn gray stays gray, because those are things on a
# board rather than work, and what is drawn orange stays orange, because those
# are other projects' programs and they are carried onto this board as they are
# onto the others.
# Nothing moves: the geometry is the Arty Z7-20's to the coordinate, and the
# legend is the same.  These things change.  (1) The fit and timing figures
# under the fabric's label come off, and DE25_FIT's bars take their place,
# from this board's own fit report.  (2) The chip's label is
# the FPGA on this board: Terasic's specifications give it as
# A5EB013BB23BE4SCS, read in a browser on the board's product page.  (3) The
# memory box names the 1 GB of LPDDR4 on the board's HPS side, which the same
# page gives as shared with the FPGA, and its lines about how the Arty Z7-20's
# memory is split come off.  (3d) The words are the Agilex's: the fabric's
# label is "FPGA fabric logic", PL is FPGA and PS is HPS in the port labels, the
# Arm label and muir's box, and the Arm box names the part's two Cortex-A76 and
# two Cortex-A55 cores with their highest clocks.  (4) The HTML comments inside
# the drawing come off, because they are the Arty Z7-20's record of what that
# board has shown, and the aria-label is replaced by de25_aria().  Every other
# label is still the Arty Z7-20's.
DE25_PART = ('A5EB013BB23BE4SCS', 'Altera Agilex 5 E-series')

# The aria-label, the drawing's own comment and the page's description say
# which of this project's blocks are done on this board, and they are generated
# from DE25_STATUS by de25_status(), so that they cannot disagree with the
# colors.  With every row undone, each keeps the words it had before any block
# was colored.
DE25_NOTHING_STARTED = 'None of it is done for this board yet: no block this project builds carries a color, the parts drawn gray are components of the board, and the blocks drawn orange are programs other projects carry onto it.'

def de25_aria():
    return ('The Arty Z7-20&rsquo;s architecture drawing, drawn for the DE25-Nano, whose FPGA is one Altera Agilex 5 E-series, part A5EB013BB23BE4SCS. '
            + (de25_status() or DE25_NOTHING_STARTED) + ' '
            'The lamps at its right are drawn in the color each one lights, which on this board is green for every one of them, as its user LEDs are, and the debug cable is drawn on a GPIO header, since the board has no Pmod. '
            'HPS means Hard Processor System. '
            'Beside muir, at the right end of the Linux outline, stands ozd, the associated machine a site of these machines takes its files, its time and its host table from over Chaosnet. '
            + OZD_ON_BOARD + ' '
            'Under the fabric&rsquo;s label, two figures for the board with its memory, the disk and the display in it: '
            + cadr_fit_words('de25-nano', 'adaptive logic modules', 'M20K memory') + ' '
            'Apart from the FPGA fabric and HPS terminology, the chip&rsquo;s label, the CPU cores and their maximum clocks, the memory, the one memory port and the two processor ports&rsquo; own names and buses, the debug window&rsquo;s bridge, the HDMI transmitter, the buttons&rsquo; and the lamps&rsquo; names, the lamps&rsquo; color, the USB-Blaster III and its socket, and the cable&rsquo;s connector, the labels are the Arty Z7-20&rsquo;s and have not been redrawn for this board.')

NUMBER = ('zero one two three four five six seven eight nine ten eleven twelve thirteen '
          'fourteen fifteen sixteen seventeen eighteen nineteen twenty twenty-one '
          'twenty-two twenty-three twenty-four twenty-five').split()

# DE25_STATUS is keyed to the Arty Z7-20's own box names and geometries,
# because de25_svg() has to find each block on the Arty's page before it can
# recolor it.  Three of those boxes --- S_AXI_HP0, S_AXI_HP2 and S_AXI_HP3 ---
# are drawn on the DE25-Nano as the one F2SDRAM box its single memory port
# actually is, and two more --- M_AXI_GP0 and M_AXI_GP1 --- are drawn under
# the HPS's own names, H2F and LWH2F.  DE25_RENAME is where de25_status() and
# everything built from it learn the name the drawing actually carries, so the
# words never say a name the drawing does not.
DE25_RENAME = {'S_AXI_HP0': 'F2SDRAM', 'S_AXI_HP2': 'F2SDRAM', 'S_AXI_HP3': 'F2SDRAM',
               'M_AXI_GP0': 'H2F', 'M_AXI_GP1': 'LWH2F'}

def de25_status(status=None, rename=None):
    """Which of the DE25-Nano's blocks are done, in sentences, from
    DE25_STATUS: one sentence naming the blocks that are done and drawn green,
    one naming those that are not and carry no color, and one for the parts
    that are not this project's work at all.  None when nothing is done yet.
    Where several rows of DE25_STATUS are one box on the drawing (DE25_RENAME),
    that box is named once and counted once.

    BOTH ENDS OF THE COUNT HAVE THEIR OWN SENTENCE, because the general one
    reads wrong at either.  With nothing done the caller uses
    DE25_NOTHING_STARTED instead of this; with everything done, "Of the
    twenty-one blocks, twenty-one are done" says the number twice and promises
    a remainder that never arrives, so it becomes "All twenty-one blocks ...
    are done" and the second sentence is simply not there."""
    status = DE25_STATUS if status is None else status
    rename = DE25_RENAME if rename is None else rename
    named = [(rename.get(name, name), s) for name, _, s in status]
    by_name = {}
    order = []
    for name, s in named:
        if name not in by_name:
            by_name[name] = s
            order.append(name)
        else:
            assert by_name[name] == s, (name, by_name[name], s)
    rows = [(name, by_name[name]) for name in order]
    total = len(rows)
    assert total < len(NUMBER), total
    def listed(names):
        return names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' and ' + names[-1]
    done = [name for name, s in rows if s == 'd-done']
    undone = [name for name, s in rows if s == '']
    assert len(done) + len(undone) == total, rows
    if not done:
        return None
    if not undone:
        out = ['All %s blocks this project builds for this board are done and drawn green: %s.'
               % (NUMBER[total], listed(done))]
    else:
        out = ['Of the %s blocks this project builds for this board, %s %s done and drawn green: %s.'
               % (NUMBER[total], NUMBER[len(done)], 'is' if len(done) == 1 else 'are', listed(done))]
        out.append('The other %s %s not done and %s no color: %s.'
                   % (NUMBER[len(undone)], 'is' if len(undone) == 1 else 'are',
                      'carries' if len(undone) == 1 else 'carry', listed(undone)))
    # No typographic entity anywhere in these sentences: they go into an HTML
    # comment as well as into an attribute, and a comment shows an entity as
    # the letters that spell it.
    out.append('The parts drawn gray are components of the board, and muir, ozd and U-Boot are drawn orange, '
               'as programs other projects carry onto this board.')
    return ' '.join(out)

def de25_comment():
    """The comment at the head of the DE25-Nano's drawing.  With nothing done
    it is the comment the drawing had then, word for word and line for
    line; otherwise the status sentences take the place of "nothing started"
    and the comment is wrapped to the same measure."""
    status = de25_status()
    if status is None:
        return '''          <!-- The Arty Z7-20's drawing, generated for the DE25-Nano with
               nothing started: no block is colored, the figures under the
               fabric's label show zero because there is no build, and the
               chip and the memory carry this board's parts, and the
               lamps are green, as this board's user LEDs are, and the
               debug cable's connector is a GPIO header, the board having no
               Pmod.  Why each thing
               is where it is, is in the Arty Z7-20's page. -->
'''
    import textwrap
    text = ("The Arty Z7-20's drawing, generated for the DE25-Nano. " + status +
            " The figures under the fabric's label are this board's own fit, as ALMs and"
            " M20K, the"
            " chip and the memory carry this board's parts, the lamps are drawn in the color"
            " each one lights, green for all of them as this board's user LEDs are, and the"
            " debug cable's connector is a GPIO header, the"
            " board having no Pmod. Why each thing is where it is, is in the Arty Z7-20's page.")
    assert '--' not in text
    return textwrap.fill(text, width=78, initial_indent='          <!-- ', subsequent_indent=' ' * 15,
                         fix_sentence_endings=True, break_on_hyphens=False) + ' -->\n'

def de25_description():
    # Three readings, for the same reason de25_status() has two: "where they
    # are done" names a distinction that has stopped existing once every block
    # is green, and a description that draws a line through nothing is a
    # description that misleads.
    if de25_status() is None:
        tail = 'with nothing on it done yet.'
    elif all(s for _, _, s in DE25_STATUS):
        tail = 'with every block this project builds for this board colored green.'
    else:
        tail = 'with this project&rsquo;s own blocks colored green where they are done on this board.'
    return ('The DE25-Nano, a board for muir-fpga with one Altera Agilex 5 E-series, part A5EB013BB23BE4SCS: the Arty Z7-20&rsquo;s architecture drawing, '
            + tail)

# WHOSE WORK EACH DE25-NANO BLOCK IS, and the one place it is set.  Every block
# this project builds is a row here: the name is the label drawn in the block,
# the geometry is its d-box rect's, and the status is 'd-done' where the block
# is done on this board and '' where it is not.  Nothing else belongs in this
# column, because nothing else is a question about this project's own work:
# the board's own parts are gray in the drawing this one is generated from,
# and the programs other projects carry here are orange in it.
# de25_svg() checks that the rows are exactly the Arty Z7-20's green blocks,
# that each geometry is followed by its name, and that no other block is
# colored green.  To recolor a block, change its status here and run gen.py.
#
# TV, Color TV, the I/O board and the serial line were amber here under the
# older five-step key, which held a block back until silicon had shown it; the
# key no longer makes that distinction, and all four are built and checked on
# this board.  THE DEBUG CABLE ADAPTER WAS THE LAST ROW WITHOUT A COLOR AND IT
# HAS ONE NOW, so every row here is green and the sentences de25_status()
# writes have no "the other one" to name.  The connector is in every build of
# this board's top level, every module under it is checked, its timing
# exceptions reach the pads they name, and the fit places all eight signals.
# What has not happened is that no ribbon from a 2x20 header to a Pmod has
# been made, so nothing of it has run on this board --- which is a question
# this column does not answer.  The front page's table does answer it, by a
# different rule, and says yes there with a qualification.
DE25_STATUS = [
    # the fabric
    ('display output',      'x="-160" y="274" width="180" height="112"', 'd-done'),
    ('S_AXI_HP3',           'x="-150" y="428" width="160" height="38"',  'd-done'),
    ('clock',               'x="40" y="62" width="112" height="128"',    'd-done'),
    ('ICMEM board',         'x="152" y="62" width="224" height="56"',    'd-done'),
    ('CADR board',          'x="152" y="118" width="224" height="72"',   'd-done'),
    ('bus interface',       'x="596" y="62" width="254" height="128"',   'd-done'),
    ('debug cable adapter', 'x="1068" y="96" width="188" height="64"',   'd-done'),
    ('Xbus to DDR',         'x="40" y="274" width="156" height="112"',   'd-done'),
    ('disk controller',     'x="210" y="274" width="200" height="112"',  'd-done'),
    ('TV',                  'x="424" y="274" width="146" height="112"',  'd-done'),
    ('Color TV',            'x="584" y="274" width="146" height="112"',  'd-done'),
    ('I/O board',           'x="780" y="274" width="210" height="112"',  'd-done'),
    ('S_AXI_HP0',           'x="38" y="428" width="160" height="38"',    'd-done'),
    ('S_AXI_HP2',           'x="230" y="428" width="160" height="38"',   'd-done'),
    ('M_AXI_GP0',           'x="640" y="428" width="410" height="38"',   'd-done'),
    ('M_AXI_GP1',           'x="1092" y="428" width="140" height="38"',  'd-done'),
    # the processing system
    ('SPL',                 'x="61" y="527" width="44" height="30"',     'd-done'),
    ('terminal',            'x="240" y="542" width="130" height="96"',   'd-done'),
    ('Chaosnet',            'x="387" y="542" width="130" height="96"',   'd-done'),
    ('serial',              'x="534" y="542" width="130" height="96"',   'd-done'),
    ('disk packs',          'x="681" y="542" width="130" height="96"',   'd-done'),
    ('console',             'x="828" y="542" width="130" height="96"',   'd-done'),
    ('USB input',           'x="975" y="542" width="130" height="96"',   'd-done'),
]

# THE DE25-NANO'S FIT BARS under the fabric's label, where the Arty Z7-20 has
# its own resource figures.  Each row is (label, the fraction used); a bar is
# 136 units wide and its fill and per cent are rounded to one decimal, as the
# Arty Z7-20's are.  The figures are gen/facts.py's.
DE25_FIT_NOTE = '''          <!-- From the Quartus fit of the CADR with the faces and the
               display output; its figures are gen/facts.py's.
               A5E 013B: 46,800 ALMs, and 358 M20K blocks of 20 Kbit each,
               895 KB, the same convention as the Zynq boards' block RAM row.
               Source: Altera Agilex 5 E-Series Product Table, 2026.08.07, p. 3:
               https://docs.altera.com/api/khub/documents/rcQSreUhbuYGXCo7Np10cw/content
               The small memories are counted inside the ALMs, as the
               lookup-table memory on the Zynq boards is counted inside the
               slices. -->
'''

def fit_bars(rows, y=68):
    out = ''
    for label, used in rows:
        # The percentage keeps one decimal always, as the Arty Z7-20's own
        # hand-written figures do; num() would strip
        # a trailing zero, which reads as a different number of significant
        # figures than the same board's other row.
        out += ('          <text class="d-s" x="-164" y="%d">%s</text>\n'
                '          <rect class="d-box" x="-164" y="%d" width="136" height="13"/>\n'
                '          <rect x="-164" y="%d" width="%s" height="13" fill="currentColor" fill-opacity="0.42"/>\n'
                '          <text class="d-n" x="%s" y="%d">%.1f%%</text>\n'
                % (y, label, y + 6, y + 6, num(round(136 * used, 1)),
                   # a fill too short to hold its percentage has it after the fill
                   num(round(-164 + 136 * used + 6, 1)) if 136 * used < 36.5 else '-158',
                   y + 16, round(100 * used, 1)))
        y += 36
    return out

def de25_svg():
    svg = board_svg('arty-z7-20.html')
    # (1) the fit figures, from their comment to the worst setup slack under
    # the two bars.  The span has to reach past the last bar's percentage to
    # that line, or the Arty Z7-20's own slack would be left standing on this
    # board's drawing, where the DE25-Nano's own lands on the same coordinate.
    # The assertions name every figure inside the span, so a figure that moves
    # out of it stops the run rather than being carried over.
    i = svg.index(FIT_NOTE)
    _, j = fit_span(svg)
    svg = svg[:i] + svg[j:]
    # No drawn slack label survives.  The Arty Z7-20's aria-label still names
    # its own slack in words at this point; that whole attribute is replaced
    # by de25_aria() at step (4), so only a <text> would be a figure left over.
    assert '>worst setup' not in svg
    # Each block of this project's takes its color from DE25_STATUS: first the
    # Arty Z7-20's green comes off every one of them, then the table puts it
    # back where this board has it.  Only the green is touched.  A block drawn
    # orange is another project's program and a block drawn gray is a part of
    # the board, and neither is a question this table answers, so both carry
    # over from the Arty Z7-20's drawing untouched.
    stripped = []
    def strip(m):
        stripped.append(m.group(1))
        return '<rect class="d-box" %s/>' % m.group(1)
    svg, n = re.subn(r'<rect class="d-box d-done" ([^/>]*)/>', strip, svg)
    assert n == 23, n
    assert not re.search(r'class="[^"]*\bd-done\b(?![^"]*\bd-key\b)[^"]*"', svg)
    assert 'd-built' not in svg and 'd-wip' not in svg, 'the retired five-step key is still in the drawing'
    assert sorted(stripped) == sorted(g for _, g, _ in DE25_STATUS), 'DE25_STATUS is not the Arty Z7-20\'s green blocks'
    for name, geom, status in DE25_STATUS:
        assert status in ('', 'd-done'), (name, status)
        rect = '<rect class="d-box" %s/>' % geom
        assert re.search(re.escape(rect) + r'\n[ \t]*<text class="d-[tm]"[^>]*>%s</text>' % re.escape(name), svg), name
        if status:
            svg = sub(svg, rect, '<rect class="d-box %s" %s/>' % (status, geom))
    colored = re.findall(r'class="[^"]*\bd-done\b(?![^"]*\bd-key\b)[^"]*"', svg)
    assert len(colored) == sum(1 for *_, s in DE25_STATUS if s), colored
    # (2) the chip
    svg = sub(svg, '<text class="d-s" x="-164" y="24">AMD Zynq 7020 &middot; XC7Z020-1CLG400C</text>',
              '<text class="d-s" x="-164" y="24">%s &middot; %s</text>' % (DE25_PART[1], DE25_PART[0]))
    # (3) the memory
    svg = sub(svg, mem_block('arty'), mem_block('de25'))
    svg = sub(svg, '<text class="d-t" x="87" y="738" text-anchor="middle">512 MB DDR3</text>',
              '<text class="d-t" x="87" y="738" text-anchor="middle">1 GB LPDDR4</text>')
    # (3b) the lamps: every user LED on this board is green (the rev B user
    # manual, section 3.7.1), so no lamp is drawn red or blue.
    lamps = re.findall(r'<circle [^>]*cx="1380"[^>]*/>', svg)
    assert len(lamps) == 8, len(lamps)
    for c in lamps:
        svg = sub(svg, c, re.sub(r'(fill|stroke)="#(?:d1495b|0969da)"', r'\1="#2da44e"', c))
    assert not re.search(r'<circle [^>]*cx="1380"[^>]*#(?:d1495b|0969da)', svg)
    # (3c) the debug cable's connector: the board has no Pmod, and the cable
    # will take pins on one of its two 2x20 GPIO headers, which pins not chosen.
    svg = sub(svg, '<text class="d-t" x="1441" y="110" text-anchor="middle">Pmod JA</text>',
              '<text class="d-t" x="1441" y="110" text-anchor="middle">GPIO header</text>')
    # (3d) the Agilex's words, and its Arm cores
    svg = sub(svg, '<text class="d-s" x="-164" y="48">Programmable Logic</text>',
              '<text class="d-s" x="-164" y="48">FPGA fabric logic</text>')
    svg = sub(svg, 'text-anchor="middle">PL masters, 64 bits, AXI3</text>',
              'text-anchor="middle">FPGA masters, 64 bits, AXI3</text>', 3)
    # Both processor-to-fabric bridges are AXI4, and the main one is not 32
    # bits in the reference design (boards/de25-nano/README.md, "The faces on
    # the two bridges" and the table of counterparts).
    svg = sub(svg, 'text-anchor="middle">PS masters, 32 bits, AXI3</text>',
              'text-anchor="middle">HPS masters, AXI4</text>', 2)
    svg = sub(svg, '<text class="d-s" x="-164" y="520.4">PS &mdash; Arm</text>',
              '<text class="d-s" x="-164" y="520.4">HPS &mdash; Arm</text>')
    svg = sub(svg, '''          <text class="d-t" x="-7" y="566" text-anchor="middle">2 &times; Cortex-A9</text>
          <text class="d-s" x="-7" y="586" text-anchor="middle">650 MHz, Linux</text>
''', '''          <text class="d-t" x="-7" y="560" text-anchor="middle">2 &times; Cortex-A76</text>
          <text class="d-s" x="-7" y="574" text-anchor="middle">up to 1.4 GHz</text>
          <text class="d-t" x="-7" y="594" text-anchor="middle">2 &times; Cortex-A55</text>
          <text class="d-s" x="-7" y="608" text-anchor="middle">up to 1.25 GHz</text>
          <text class="d-s" x="-7" y="628" text-anchor="middle">Linux</text>
''')
    svg = sub(svg, '<text class="d-s" x="1162" y="586" text-anchor="middle">on the PS,</text>',
              '<text class="d-s" x="1162" y="586" text-anchor="middle">on the HPS,</text>')
    # (5) THE ONE MEMORY PORT.  This board has a single fabric-to-SDRAM bridge
    # rather than the Zynq's three HP ports, and all three fabric masters ---
    # the display, the machine's own memory bridge, and the disk controller's
    # second leg --- share it through an arbiter that gives the machine
    # priority.  The three boxes become one, spanning their own left and
    # right edges (S_AXI_HP3's at -150 to S_AXI_HP2's at 390) so that every
    # line that used to land on one of the three still lands on this one
    # without moving.  The three separate lines down to the SDRAM controller
    # become the one the port itself now is.
    svg = sub(svg, '''          <rect class="d-plate" x="-150" y="428" width="160" height="38"/>
          <rect class="d-box d-done" x="-150" y="428" width="160" height="38"/>
          <text class="d-m" x="-70" y="446" text-anchor="middle">S_AXI_HP3</text>
          <text class="d-s" x="-70" y="460" text-anchor="middle">FPGA masters, 64 bits, AXI3</text>
''', '''          <rect class="d-plate" x="-150" y="428" width="540" height="38"/>
          <rect class="d-box d-done" x="-150" y="428" width="540" height="38"/>
          <text class="d-m" x="120" y="446" text-anchor="middle">F2SDRAM</text>
          <text class="d-s" x="120" y="460" text-anchor="middle">fabric masters, 64 bits, AXI4, one port shared by burst</text>
''')
    svg = sub(svg, '''          <rect class="d-plate" x="38" y="428" width="160" height="38"/>
          <rect class="d-box d-done" x="38" y="428" width="160" height="38"/>
          <text class="d-m" x="118" y="446" text-anchor="middle">S_AXI_HP0</text>
          <text class="d-s" x="118" y="460" text-anchor="middle">FPGA masters, 64 bits, AXI3</text>
''', '')
    svg = sub(svg, '''          <rect class="d-box d-done" x="230" y="428" width="160" height="38"/>
          <text class="d-m" x="310" y="446" text-anchor="middle">S_AXI_HP2</text>
          <text class="d-s" x="310" y="460" text-anchor="middle">FPGA masters, 64 bits, AXI3</text>
''', '')
    svg = sub(svg, '<path class="d-line" d="M-70,466 L-70,652"/>',
              '<path class="d-line" d="M120,466 L120,652"/>')
    svg = sub(svg, '          <path class="d-line" d="M118,466 L118,652"/>\n', '')
    svg = sub(svg, '          <path class="d-line" d="M240,466 L240,494 L170,494 L170,652"/>\n', '')
    svg = sub(svg, '<path class="d-dash" d="M-170,450 L-150,450 M10,450 L38,450 M198,450 L230,450 M390,450 L640,450 M1050,450 L1092,450 M1232,450 L1351,450"/>',
              '<path class="d-dash" d="M-170,450 L-150,450 M390,450 L640,450 M1050,450 L1092,450 M1232,450 L1351,450"/>')
    # (6) THE TWO PROCESSOR PORTS ARE NAMED FOR THE HPS'S OWN BRIDGES, not the
    # Zynq's: M_AXI_GP0 is H2F, the main bridge, and M_AXI_GP1 is LWH2F, the
    # lightweight one the console and the debug cable sit behind.  Geometry,
    # status and every other label are untouched.
    svg = sub(svg, '<text class="d-m" x="845" y="446" text-anchor="middle">M_AXI_GP0</text>',
              '<text class="d-m" x="845" y="446" text-anchor="middle">H2F</text>')
    svg = sub(svg, '<text class="d-m" x="1162" y="446" text-anchor="middle">M_AXI_GP1</text>',
              '<text class="d-m" x="1162" y="446" text-anchor="middle">LWH2F</text>')
    svg = sub(svg, '<text class="d-s" x="893" y="600" text-anchor="middle">over M_AXI_GP1</text>',
              '<text class="d-s" x="893" y="600" text-anchor="middle">over LWH2F</text>')
    # The debug cable's window is on the lightweight bridge, at 0x2000_1000
    # (boards/de25-nano/README.md, "The faces on the two bridges").
    svg = sub(svg, '<text class="d-s" x="1162" y="152" text-anchor="middle">registers at GP1 + 0x1000</text>',
              '<text class="d-s" x="1162" y="152" text-anchor="middle">registers at LWH2F + 0x1000</text>')
    # (8) THE BOARD'S OWN PARTS BY THEIR OWN NAMES, from
    # boards/de25-nano/README.md: the ADV7513 does the HDMI encoding, so the
    # fabric sends it no TMDS; the buttons are KEY0 and KEY1 and the lamps
    # LEDR0 to LEDR5; the console and JTAG share the USB-Blaster III's one
    # Type-C socket.  The Arty Z7-20's "four ports, arbitrated in hardware"
    # under the memory controller is not confirmed for this board's HPS
    # controller by any source here, so the claim comes off rather than being
    # guessed.  The USB host port stays: docs/board.md, "A keyboard at the
    # board", says the board has one and Linux drives it.
    svg = sub(svg, 'over the first; TMDS to HDMI</text>', 'over the first; to the ADV7513</text>')
    svg = sub(svg, '          <text class="d-s" x="87" y="684" text-anchor="middle">four ports, arbitrated in hardware</text>\n', '')
    svg = sub(svg, '>BTN0 &mdash; BOOT</text>', '>KEY0 &mdash; BOOT</text>')
    svg = sub(svg, '>BTN1 &mdash; RESET</text>', '>KEY1 &mdash; RESET</text>')
    for n in range(6):
        svg = sub(svg, '>LD%d &mdash; ' % n, '>LEDR%d &mdash; ' % n)
    svg = sub(svg, '''          <text class="d-t" x="897" y="738" text-anchor="middle">USB-UART</text>
          <text class="d-t" x="897" y="756" text-anchor="middle">/ JTAG</text>
          <text class="d-s" x="897" y="778" text-anchor="middle">one micro-USB socket,</text>''',
              '''          <text class="d-t" x="897" y="738" text-anchor="middle">USB-Blaster III</text>
          <text class="d-s" x="897" y="778" text-anchor="middle">one USB-C socket,</text>''')
    # (7) THE LINUX OUTLINE IS NOT COLORED.  It is a container and not a
    # component: the blocks standing inside it carry the status, and it
    # carries only its own dotted stroke.  A tinted outline reads as a claim
    # about a thing, and the thing it would be claiming about is already
    # drawn inside it.
    # (4) the comments and the aria-label
    svg, n = re.subn(r'\n[ \t]*<!--.*?-->[ \t]*(?=\n)', '', svg, flags=re.S)
    assert '<!--' not in svg, 'a comment is not on a line of its own'
    svg, n = re.subn(r'aria-label="[^"]*"', 'aria-label="%s"' % de25_aria(), svg, count=1)
    assert n == 1
    # (1) the fit bars, after (4) so that their note stays
    label = '          <text class="d-s" x="-164" y="48">FPGA fabric logic</text>\n'
    f = F.fit('de25-nano', 'cadr')
    svg = sub(svg, label, label + DE25_FIT_NOTE + fit_bars(F.fit_rows(f))
                   + slack_block(F.setup(f)) + '\n')
    svg = sub(svg, '''">

          <rect class="d-box d-done d-key"''', '''">

%s          <rect class="d-box d-done d-key"''' % de25_comment())
    return svg

def build_de25():
    board_page('de25-nano.html', 'DE25-Nano', 'muir-fpga — the MIT CADR on a DE25-Nano',
               de25_description(),
               'QUUX and the CADR mapped onto one Altera Agilex 5 E-series, the A5EB013B.',
               "muir-fpga's board, waving",
               (('booting.html', 'How it boots'), ('debugging.html', 'The debug cable')) + BOARD_KEYS['de25-nano.html'],
               TERASIC_DE25, de25_svg(), quux=quux_svg('de25-nano'))

# ============================================================ THE KRIA KR260

# THE KRIA KR260'S PAGE.  Its drawing is the Arty Z7-20's, generated from it as
# the DE25-Nano's is, and nothing moves that the board does not change.  What
# the board changes, from muir-fpga's boards/kria-kr260/ and its K2 to K4 runs
# (the card, Linux, the PS8's ports and the top level): (1) the part is a
# Zynq UltraScale+ XCK26 and its processing system four Cortex-A53 cores; (2)
# the factory U-Boot in the board's flash is left alone, so what stood for the
# Arty Z7-20's own first stage is the flash, gray, and U-Boot is gray too, a
# part of the board as it comes and not a program carried onto it; (3) the
# tick is the carrier's 25 MHz through an MMCM; (4) every port is 128 bits
# wide and the fabric's adapters meet it at that width; main memory is on
# S_AXI_HP0_FPD and the pack side on S_AXI_HP2_FPD, the faces on
# M_AXI_HPM0_FPD and the console and debug window on M_AXI_HPM1_FPD; (5) the
# board has no HDMI: its one video connector is the processing system's
# DisplayPort, which the display output feeds through S_AXI_HP3_FPD, and the
# debug cable adapter carries no color, which is what a block not done on a
# board looks like here;
# (6) the card is a USB disk to the loader, and the keyboard is on the other
# USB controller; (7) the lamps are UF1 and UF2, there is no button and no
# switch, and the SOM's fan is its own box; (8) the debug cable is PMOD1.
KR260_PART = ('XCK26-SFVC784-2LV-C', 'AMD Zynq UltraScale+')
KR260_RENAME = {'S_AXI_HP0': 'S_AXI_HP0_FPD', 'S_AXI_HP2': 'S_AXI_HP2_FPD', 'S_AXI_HP3': 'S_AXI_HP3_FPD',
                'M_AXI_GP0': 'M_AXI_HPM0_FPD', 'M_AXI_GP1': 'M_AXI_HPM1_FPD'}
KR260_STATUS = [(n, g, ('' if n == 'debug cable adapter' else s))
                for n, g, s in DE25_STATUS if n != 'SPL']


def kr260_aria():
    return ('The CADR mapped onto one Zynq UltraScale+ XCK26, part XCK26-SFVC784-2LV-C, on a Kria KR260. '
            + (de25_status(KR260_STATUS, KR260_RENAME) or DE25_NOTHING_STARTED) + ' '
            'The fabric&rsquo;s clock is the carrier&rsquo;s 25 megahertz through a clock manager, 100 megahertz, ten nanoseconds a tick. '
            'Under the fabric&rsquo;s label, ' + cadr_fit_words('kria-kr260') + ' '
            'Every port to the processing system is 128 bits wide and adapters in the fabric meet it at that width. '
            'Main memory is on the first of the high-performance ports and the disk packs on the third; the faces are on the first master port and the console and the debug window on the second. '
            'The board has no HDMI: its video connector, J6, is the processing system&rsquo;s DisplayPort, wired to the DisplayPort controller drawn gray in the processing system, ' + F.display('kria-kr260') + '. The display output in the fabric sends that controller its pixels by a line, through the fourth high-performance port. '
            'The boot loader is the board&rsquo;s own, in its flash, and is left alone: it reads the microSD card, which is a USB disk to it, or a server on the network. '
            'The two lamps, UF1 and UF2, are green and carry the microcycles and the error halt; there is no button and no switch; the fan is driven on. '
            'The debug cable is on PMOD1. '
            'Beside muir, at the right end of the Linux outline, stands ozd, the associated machine a site of these machines takes its files, its time and its host table from over Chaosnet. '
            + OZD_ON_BOARD + ' '
            'The parts drawn gray are components of the board, and muir, ozd and U-Boot are drawn orange, '
            'as programs other projects carry onto this board.')

def kr260_comment():
    import textwrap
    text = ("The Arty Z7-20's drawing, generated for the Kria KR260. "
            + (de25_status(KR260_STATUS, KR260_RENAME) or DE25_NOTHING_STARTED)
            + " The loader is the board's own, in its flash, and is gray. The lamps UF1 and UF2 are green.")
    assert '--' not in text
    return textwrap.fill(text, width=78, initial_indent='          <!-- ', subsequent_indent=' ' * 15,
                         fix_sentence_endings=True, break_on_hyphens=False) + ' -->\n'

def kr260_description():
    return ('The Kria KR260, a board for muir-fpga with one AMD Zynq UltraScale+ XCK26: the Arty Z7-20&rsquo;s architecture drawing for the CADR and for QUUX, '
            'with this project&rsquo;s own blocks colored green where they are done on this board.')

def kria_loader(svg):
    """The flash and the factory U-Boot are the board's own, not a program carried onto it."""
    svg = sub(svg, '''          <rect class="d-box d-done" x="61" y="527" width="44" height="30"/>
          <text class="d-t" x="83" y="547" text-anchor="middle">SPL</text>
''', '''          <rect class="d-box d-ext" x="61" y="527" width="44" height="30"/>
          <text class="d-t" x="83" y="547" text-anchor="middle">QSPI</text>
''')
    svg = sub(svg, '<rect class="d-dot d-part" x="56" y="522" width="54" height="124"/>',
              '<rect class="d-dot d-ext" x="56" y="522" width="54" height="124"/>')
    return svg

def kria_display(svg):
    """The HDMI box comes off; the DisplayPort controller and J6 stand in the processing system's row."""
    # The DisplayPort controller is the processing system's own, so it is drawn
    # gray in the processing system's row of controllers, and J6 below the chip
    # like the other connectors.  The display output in the fabric, which is
    # built and green, sends it pixels by a line down the left
    # margin into its top.  The connector box the Arty Z7-20's drawing has at
    # the chip's left edge comes off.
    svg = sub(svg, '''          <path class="d-line" d="M-160,330 L-183,330"/>\n''', '')
    svg = sub(svg, '''          <rect class="d-box d-ext" x="-283" y="288" width="100" height="84"/>
          <text class="d-t" x="-233" y="310" text-anchor="middle">HDMI out</text>
          <text class="d-s" x="-233" y="330" text-anchor="middle">the display,</text>
          <text class="d-s" x="-233" y="344" text-anchor="middle">from the fabric,</text>
          <text class="d-s" x="-233" y="358" text-anchor="middle">1280 &times; 1024, 60 Hz</text>
''', '''          <path class="d-line" d="M-160,360 L-195,360 L-195,632 L-137,632 L-137,652"/>
          <rect class="d-plate" x="-180" y="652" width="86" height="40"/>
          <rect class="d-box d-ext" x="-180" y="652" width="86" height="40"/>
          <text class="d-t" x="-137" y="670" text-anchor="middle">DisplayPort</text>
          <text class="d-s" x="-137" y="684" text-anchor="middle">controller</text>
          <path class="d-line" d="M-137,692 L-137,712"/>
          <rect class="d-box d-ext" x="-180" y="712" width="86" height="84"/>
          <text class="d-t" x="-137" y="738" text-anchor="middle">DisplayPort</text>
          <text class="d-s" x="-137" y="762" text-anchor="middle">J6, 1.2a,</text>
          <text class="d-s" x="-137" y="776" text-anchor="middle">%s</text>
''' % F.display('kria-kr260', ' &times; '))
    svg = sub(svg, '<text class="d-s" x="-164" y="520.4">PS &mdash; Arm</text>',
              '<text class="d-s" x="-156" y="520.4">PS &mdash; Arm</text>')
    return svg

def kria_ports(svg):
    """The ports: 128 bits, and the part's own names."""
    for o, n in (('>S_AXI_HP3</text>', '>S_AXI_HP3_FPD</text>'), ('>S_AXI_HP0</text>', '>S_AXI_HP0_FPD</text>'),
                 ('>S_AXI_HP2</text>', '>S_AXI_HP2_FPD</text>'), ('>M_AXI_GP0</text>', '>M_AXI_HPM0_FPD</text>'),
                 ('>M_AXI_GP1</text>', '>M_AXI_HPM1_FPD</text>')):
        svg = sub(svg, o, n)
    svg = sub(svg, 'text-anchor="middle">PL masters, 64 bits, AXI3</text>', 'text-anchor="middle">FPGA masters, 128 bits</text>', 3)
    svg = sub(svg, '<text class="d-s" x="845" y="460" text-anchor="middle">PS masters, 32 bits, AXI3</text>',
              '<text class="d-s" x="845" y="460" text-anchor="middle">Arm masters, 128 bits, the faces in 32-bit lanes</text>')
    svg = sub(svg, '<text class="d-s" x="1162" y="460" text-anchor="middle">PS masters, 32 bits, AXI3</text>',
              '<text class="d-s" x="1162" y="460" text-anchor="middle">Arm masters, 128-bit</text>')
    return svg

def kria_ps(svg, bitstream=('the CADR&rsquo;s bitstream,', 'the CADR&rsquo;s bitstream,')):
    """The processing system, the memory's total and the foot, as the Kria KR260 has them."""
    svg = sub(svg, '''          <text class="d-t" x="-7" y="566" text-anchor="middle">2 &times; Cortex-A9</text>
          <text class="d-s" x="-7" y="586" text-anchor="middle">650 MHz, Linux</text>
''', '''          <text class="d-t" x="-7" y="566" text-anchor="middle">4&times;Cortex-A53</text>
          <text class="d-s" x="-7" y="586" text-anchor="middle">up to 1.33 GHz</text>
          <text class="d-s" x="-7" y="600" text-anchor="middle">Linux</text>
''')
    svg = sub(svg, '<text class="d-s" x="87" y="684" text-anchor="middle">four ports, arbitrated in hardware</text>',
              '<text class="d-s" x="87" y="684" text-anchor="middle">HP0 shares a port with the DisplayPort DMA</text>')
    svg = sub(svg, '''          <text class="d-t" x="87" y="738" text-anchor="middle">512 MB DDR3</text>''',
              '''          <text class="d-t" x="87" y="738" text-anchor="middle">4 GB DDR4</text>''')
    svg = sub(svg, '<text class="d-s" x="453" y="684" text-anchor="middle">gigabit Ethernet</text>',
              '<text class="d-s" x="453" y="684" text-anchor="middle">J10C, gigabit Ethernet</text>')
    svg = sub(svg, '''          <text class="d-t" x="746" y="670" text-anchor="middle">SD host</text>
          <text class="d-s" x="746" y="684" text-anchor="middle">the card</text>''',
              '''          <text class="d-t" x="746" y="670" text-anchor="middle">USB 0</text>
          <text class="d-s" x="746" y="684" text-anchor="middle">the card, as a USB disk</text>''')
    svg = sub(svg, '''          <text class="d-t" x="1040" y="670" text-anchor="middle">USB host</text>''',
              '''          <text class="d-t" x="1040" y="670" text-anchor="middle">USB 1</text>''')
    svg = sub(svg, '''          <text class="d-t" x="746" y="738" text-anchor="middle">microSD</text>
          <text class="d-s" x="746" y="758" text-anchor="middle">U-Boot, %s</text>''' % bitstream[0],
              '''          <text class="d-t" x="746" y="738" text-anchor="middle">microSD, J11</text>
          <text class="d-s" x="746" y="758" text-anchor="middle">boot.scr, %s</text>''' % bitstream[1])
    return svg

def kria_right(svg):
    """The right column: the two lamps and the fan; no button, no switch."""
    a = svg.index('          <rect class="d-box d-ext" x="1366" y="264" width="150" height="66"/>')
    endm = '          <path class="d-line" d="M1351,243 L1366,243"/>\n'
    assert svg.count(endm) == 1
    z = svg.index(endm) + len(endm)
    svg = svg[:a] + '''          <rect class="d-box d-ext" x="1366" y="264" width="150" height="66"/>
          <circle cx="1380" cy="283" r="8" fill="none" stroke="#2da44e" stroke-width="1" stroke-opacity="0.5"/>
          <circle class="d-lamp-fast" cx="1380" cy="283" r="4.5" fill="#2da44e" fill-opacity="1" stroke="currentColor" stroke-width="1"/>
          <text class="d-s" x="1394" y="287">UF1 &mdash; microcycles</text>
          <circle cx="1380" cy="309" r="8" fill="none" stroke="#2da44e" stroke-width="1" stroke-opacity="0.5"/>
          <circle class="d-lamp-slow" cx="1380" cy="309" r="4.5" fill="#2da44e" fill-opacity="1" stroke="currentColor" stroke-width="1"/>
          <text class="d-s" x="1394" y="313">UF2 &mdash; error halt</text>
          <path class="d-line" d="M1351,297 L1366,297"/>
          <rect class="d-box d-ext" x="1366" y="336" width="150" height="48"/>
          <text class="d-t" x="1441" y="356" text-anchor="middle">Fan</text>
          <text class="d-s" x="1441" y="372" text-anchor="middle">driven on, low is on</text>
          <path class="d-line" d="M1351,360 L1366,360"/>
''' + svg[z:]
    return svg

def kria_border(svg):
    # THE CHIP'S LEFT BORDER MOVES OUT BY SIXTY.  The line from the display
    # output to the DisplayPort controller runs down the left margin and keeps
    # clear room either side, and the border stands well to the left of the
    # connector's box below the chip, so that the two edges do not read as one
    # line.  The labels in the column at the border's left go out with it (the
    # chip's name, the fabric's label, the bars and the notes under them); the
    # processing system's label stands to the right of the line.
    svg = sub(svg, '<rect class="d-box" x="-170" y="28" width="1521" height="668.5"/>',
              '<rect class="d-box" x="-230" y="28" width="1581" height="668.5"/>')
    svg = sub(svg, 'd="M-170,450 L-150,450', 'd="M-230,450 L-150,450')
    def out(m):
        x, y = float(m.group(1)), float(m.group(2))
        # to 240: QUUX's drawing has a third bar, which moves its notes down
        if -170 < x < -100 and (y <= 240 or y == 520.4):
            return 'x="%s" y="%s"' % (num(round(x - 60, 1)) if y <= 240 else '-183', m.group(2))
        return m.group(0)
    svg = re.sub(r'x="(-?[\d.]+)" y="([\d.]+)"', out, svg)
    return svg

def kr260_svg():
    svg = board_svg('arty-z7-20.html')
    # the comments first, as they are the Arty Z7-20's record of what that board has shown
    svg, n = re.subn(r'\n[ \t]*<!--.*?-->[ \t]*(?=\n)', '', svg, flags=re.S)
    assert '<!--' not in svg
    # (1) the fit figures come off, and the machine's own text takes their place
    i, j = fit_span(svg)
    f = F.fit('kria-kr260', 'cadr')
    bars = F.fit_rows(f)
    down = 36 * (len(bars) - 2)
    svg = (svg[:i] + fit_bars(bars) + slack_block(F.setup(f), 140 + down) + '''
          <text class="d-s" x="-164" y="%d">adapters in the fabric</text>
          <text class="d-s" x="-164" y="%d">meet every port at</text>
          <text class="d-s" x="-164" y="%d">128 bits</text>
''' % (170 + down, 184 + down, 198 + down) + svg[j:])
    svg = kria_loader(svg)
    # (3) colors from KR260_STATUS
    stripped = []
    def strip(m):
        stripped.append(m.group(1))
        return '<rect class="d-box" %s/>' % m.group(1)
    svg, n = re.subn(r'<rect class="d-box d-done" ([^/>]*)/>', strip, svg)
    assert n == 22, n
    assert sorted(stripped) == sorted(g for _, g, _ in KR260_STATUS), 'KR260_STATUS is not the Arty Z7-20\'s green blocks'
    for name, geom, status in KR260_STATUS:
        rect = '<rect class="d-box" %s/>' % geom
        assert re.search(re.escape(rect) + r'\n[ \t]*<text class="d-[tm]"[^>]*>%s</text>' % re.escape(name), svg), name
        if status:
            svg = sub(svg, rect, '<rect class="d-box %s" %s/>' % (status, geom))
    # (4) the chip and the clock
    svg = sub(svg, '<text class="d-s" x="-164" y="24">AMD Zynq 7020 &middot; XC7Z020-1CLG400C</text>',
              '<text class="d-s" x="-164" y="24">%s &middot; %s</text>' % (KR260_PART[1], KR260_PART[0]))
    svg = sub(svg, '''          <text class="d-s" x="96" y="142" text-anchor="middle">100 MHz,</text>
          <text class="d-s" x="96" y="156" text-anchor="middle">10 ns a tick</text>
          <text class="d-s" x="96" y="176" text-anchor="middle">15 ticks=150 ns</text>
''', '''          <text class="d-s" x="96" y="138" text-anchor="middle">25 MHz in,</text>
          <text class="d-s" x="96" y="152" text-anchor="middle">MMCM, 100 MHz,</text>
          <text class="d-s" x="96" y="166" text-anchor="middle">10 ns a tick</text>
          <text class="d-s" x="96" y="180" text-anchor="middle">15 ticks=150 ns</text>
''')
    # (5) the display: DisplayPort, not HDMI; the two screens side by side at 1:1
    svg = sub(svg, '''          <text class="d-s" x="-70" y="346" text-anchor="middle">side by side, the color one</text>
          <text class="d-s" x="-70" y="360" text-anchor="middle">over the first; TMDS to HDMI</text>
''', '''          <text class="d-s" x="-70" y="346" text-anchor="middle">side by side at 1:1, with</text>
          <text class="d-s" x="-70" y="360" text-anchor="middle">equal margins, and hands</text>
          <text class="d-s" x="-70" y="374" text-anchor="middle">them to the DisplayPort</text>
          <text class="d-s" x="-70" y="388" text-anchor="middle">controller</text>
''')
    svg = kria_display(svg)
    svg = kria_ports(svg)
    svg = sub(svg, '<text class="d-s" x="893" y="600" text-anchor="middle">over M_AXI_GP1</text>',
              '<text class="d-s" x="893" y="600" text-anchor="middle">over HPM1</text>')
    svg = sub(svg, '<text class="d-s" x="1162" y="152" text-anchor="middle">registers at GP1 + 0x1000</text>',
              '<text class="d-s" x="1162" y="152" text-anchor="middle">registers at HPM1 + 0x1000</text>')
    svg = kria_ps(svg)
    svg = sub(svg, mem_block('arty'), mem_block('kria'))
    # (8) the right column: the Pmod, the two lamps, the fan; no button, no switch
    svg = sub(svg, '<text class="d-t" x="1441" y="110" text-anchor="middle">Pmod JA</text>',
              '<text class="d-t" x="1441" y="110" text-anchor="middle">PMOD1</text>')
    svg = kria_right(svg)
    # (9) the aria-label, and the comment at the head
    svg, n = re.subn(r'aria-label="[^"]*"', 'aria-label="%s"' % kr260_aria(), svg, count=1)
    assert n == 1
    svg = sub(svg, '''">

          <rect class="d-box d-done d-key"''', '''">

%s          <rect class="d-box d-done d-key"''' % kr260_comment())
    svg = kria_border(svg)
    return svg

KR260_BODY = '''<div class="hero-description">
<p>The board&rsquo;s own loader, in its flash, is left alone: it reads the microSD card, which it sees as a USB disk, or a server on the network, and loads Linux and then the bitstream from there.</p>
<p>The tick is 10&nbsp;ns, from the carrier&rsquo;s 25&nbsp;MHz clock through a clock manager. Main memory is on the first high-performance port and every port is 128 bits wide. The two user LEDs carry the lamps: UF1 shows the microcycles, and UF2 the error halt, or a slow blink while the machine boots.</p>
<p>The CADR boots its system from its disk pack, as LISPM-1, at Chaosnet address 177201, with ozd on the board as its associated machine. A USB keyboard and mouse at the board reach the machine, and Ctrl-Alt-Del from that keyboard cold-boots it.</p>
<p>A monitor on the board&rsquo;s DisplayPort, J6, shows the machine at %s, 60&nbsp;Hz: the CADR&rsquo;s main screen and its color TV side by side at 1:1, with equal margins. The color TV is on by default on this board. After an idle time the monitor sleeps, and a key at the board wakes it; that key is swallowed. The boot chord works with the monitor asleep. The link is brought up by <code>cadr-displayport</code>, a small program of this project&rsquo;s, and two of its tables are AMD&rsquo;s, under the MIT License.</p>
<p>QUUX runs here too, in the second drawing: the 40-bit word in a pipeline of four stages, one clock each. Its memory master is 64 bits wide and reaches the 128-bit port as narrow bursts. It boots muir-sys&rsquo;s system from its own boot PROM, and its screen fills the monitor.</p>
</div>
''' % F.display('kria-kr260', '&times;')

def build_kr260():
    board_page('kria-kr260.html', 'Kria KR260', 'muir-fpga — the MIT CADR on a Kria KR260',
               kr260_description(),
               'QUUX and the CADR mapped onto one AMD Zynq UltraScale+ XCK26, on a Kria KR260.',
               "muir-fpga's board, waving",
               (('booting.html', 'How it boots'), ('debugging.html', 'The debug cable')) + BOARD_KEYS['kria-kr260.html'],
               AMD_KR260, kr260_svg(), body=KR260_BODY, quux=quux_svg('kria-kr260'),
               own_keys=(('#cable', 'The cable&rsquo;s connector'),), after=kria_cable_section())

# ============================================================ QUUX ON A BOARD

# THE QUUX DRAWINGS, one for each board that runs QUUX, shown after the CADR's.
# They are in the CADR's style and conventions --- green is this project's work
# and built and checked, orange another project's program, gray the board's own
# parts --- on the same frame, the same ports and the same foot, and what they
# draw is what muir-fpga builds for QUUX at the revision every board runs, 15:
# the 40-bit word in a pipeline of four stages, one clock each.  Read from
# muir-fpga at bbd7f1a: `rtl/machine/quux15_*.sv`, `rtl/plumbing/quux15_*.sv`,
# the boards' revision 15 tops (`boards/arty-z7-20/quux15_arty.sv`,
# `boards/kria-kr260/quux15_kr260.sv`, `boards/de25-nano/quux15_de25.sv`) and
# docs/fits.md, docs/board.md and docs/timing.md:
#   - the clock: a stage is a clock and the microcycle is the clock
#     (`quux15_core.sv`'s header), and each board runs at the period its fit
#     closes at (gen/facts.py), set in the board's top: the Arty Z7-20's 125 MHz through an MMCM, the Kria
#     KR260's 25 MHz through an MMCM, the DE25-Nano's 50 MHz through an I/O
#     PLL;
#   - the processor: the word is 40 bits, the control store 16K words
#     (`quux15_store.sv`), the PDL buffer 16K words (`quux15_core.sv`'s
#     `pdl`), MUL and DIV one instruction each (`quux_muldiv`); no map, but a
#     TLB of 4,096 entries with a walk on a miss (`quux15_mmu.sv`);
#   - the memory port and the cache (`quux15_port.sv`): a start goes to
#     memory, to the register page or nowhere (`quux15_core.sv`'s start
#     decode); block-disk's transfer is a second requester below the
#     processor, so the box does not count requesters; the cache two ways,
#     write-through, in lines of eight words, of the board's size
#     (gen/facts.py); `quux15_axi_master.sv` is the
#     master of main memory inside the core's port, 64 bits, which fills a
#     line of eight words in five beats;
#   - the register page, the device window's last page, physical `1777777400` up
#     (`quux15_core.sv`'s `REGISTER_PAGE_BUS`): the feature words, the
#     interrupt status, the three interval timers and the real-time clock
#     (`quux15_devices.sv`); keyboard and mouse (`quux15_input.sv`);
#     block-disk, its registers in `quux15_devices.sv` and its walk in
#     `quux15_block_walk.sv`; the file device's registers and the video
#     controller's mode (`quux15_devices.sv`), whose frame buffer is on the
#     memory bus, in DDR at the display's base, and whose raster the display
#     output scans out of DDR;
#   - what is not there: no bus interface and no Xbus or Unibus, no I/O board,
#     no serial line, no Chaosnet cable (the interface is built and its cable
#     tied off), no color board and no debug cable, and no ozd;
#   - on the processing system's side, the programs QUUX needs: the terminal
#     (its screen is the video controller, the board's display in
#     gen/facts.py), quux-file-device,
#     the disk packs, the console and the USB input;
#   - the buttons, switch and lamps keep the CADR's meanings where revision 15
#     has the signal (docs/board.md, "On QUUX revision 15 BTN0 does nothing",
#     "On QUUX revision 15 SW0 does nothing", "QUUX revision 15 keeps each
#     lamp's meaning where it has the signal");
#   - the memory is QUUX's own region, its main memory below the CADR's
#     display and records, so the foot says so.
# A board's period, the clock it is made from, and the top that decides it.
QUUX_CLOCK = {'arty-z7-20': ('125 MHz in,', 'MMCM,', 'quux15_arty'),
              'de25-nano': ('50 MHz in,', 'I/O PLL,', 'quux15_de25'),
              'kria-kr260': ('25 MHz in,', 'MMCM,', 'quux15_kr260')}
# The period, the cache and the fit are gen/facts.py's.
# The register ports of the processing system or hard processor system that
# the faces (the file device's page) and the console are on.
QUUX_PORTS = {'arty-z7-20': ('GP0', 'GP1'), 'de25-nano': ('H2F', 'LWH2F'), 'kria-kr260': ('HPM0', 'HPM1')}

def quux_fit_words(board, unit):
    """The fit under the fabric's label, as the aria-label says it."""
    f = F.fit(board, 'quux')
    rows = F.fit_rows(f)
    (l1, p1), (l2, p2) = rows[:2]
    more = ''.join(', and %s UltraRAM blocks, %.1f per cent' % (l.split(' ', 1)[1].replace(' of ', ' of the '), 100 * p)
                   for l, p in rows[2:])
    return ('Under the fabric&rsquo;s label, %s %s are in use, %.1f per cent, and %s of block %s, %.1f per cent%s; '
            'under those figures, the worst setup slack of this build, plus %s nanoseconds. '
            % (l1.split(' ', 1)[1].replace(' of ', ' of the '), unit, 100 * p1,
               l2.split(' ', 1)[1].replace(' of ', ' of the '), 'RAM' if unit == 'lookup tables' else 'memory',
               100 * p2, more, F.setup(f).lstrip('+')))

def quux_machine_words(board, where):
    """The blocks in the fabric, as the aria-label says them."""
    clk_in, pll, _ = QUUX_CLOCK[board]
    return ('In the %s: the clock, the board&rsquo;s %s through an %s, at a period of %s nanoseconds, one clock a stage of the four-stage pipeline; '
            'the processor, with a 40-bit word, a control store of 16K words, a PDL buffer of 16K words and multiply and divide in one instruction each; the TLB, of 4,096 entries, with a walk on a miss; '
            'the memory port, whose cycles go to the memory bus, to a device register or nowhere; the cache, %s words in two ways, write-through, in lines of eight words; '
            'the register page, with the feature words, the interrupt status, three interval timers and the real-time clock; and the console. '
            'Under the page: the memory master, whose lines of eight words arrive in five 64-bit beats, block-disk, the video controller, the file device and the keyboard and mouse. '
            % (where, clk_in.rstrip(','), pll.rstrip(','), F.period(board), F.cache_words(board)))

def quux_aria(board):
    arty = board == 'arty-z7-20'
    kria = board == 'kria-kr260'
    if kria:
        return ('QUUX mapped onto one Zynq UltraScale+ XCK26, part XCK26-SFVC784-2LV-C, on a Kria KR260: the same machine as the CADR&rsquo;s drawing before it, with QUUX&rsquo;s own blocks. '
                + quux_machine_words(board, 'programmable logic') +
                'The memory master&rsquo;s 64-bit bursts reach the processing system&rsquo;s 128-bit port as narrow bursts. '
                'There is no bus interface, no I/O board, no serial line, no Chaosnet, no color board and no debug cable, and no ozd, because QUUX has a file device and a real-time clock of its own. '
                + quux_fit_words(board, 'lookup tables') +
                'Under the chip the memory box says the areas are QUUX&rsquo;s: %s of main memory, 1 MB of display and 128 KB of disk packs. ' % F.memory(board) +
                'The board has no HDMI: its video connector, J6, is the processing system&rsquo;s DisplayPort, wired to the DisplayPort controller drawn gray in the processing system. The display output in the fabric sends that controller its pixels by a line, through the fourth high-performance port. '
                'The boot loader is the board&rsquo;s own, in its flash, and is left alone. '
                'The two lamps, UF1 and UF2, are green; there is no button and no switch; the fan is driven on. '
                'Every block this project builds that is done on this board is drawn green; the parts drawn gray are components of the board. ')
    btn, lamp = ('BTN', 'LD') if arty else ('KEY', 'LEDR')
    return ('QUUX mapped onto %s: the same machine as the CADR&rsquo;s drawing before it, with QUUX&rsquo;s own blocks. '
            % ('one AMD Zynq 7020, part XC7Z020-1CLG400C' if arty else 'one Altera Agilex 5 E-series, part A5EB013BB23BE4SCS')
            + quux_machine_words(board, 'programmable logic' if arty else 'FPGA fabric')
            + 'There is no bus interface, no I/O board, no serial line, no Chaosnet, no color board and no debug cable, and no ozd, because QUUX has a file device and a real-time clock of its own. '
            + quux_fit_words(board, 'lookup tables' if arty else 'adaptive logic modules')
            + 'Under the chip the memory box says the areas are QUUX&rsquo;s: %s of main memory, 1 MB of display and 128 KB of disk packs. ' % F.memory(board)
            + '%s0 and SW0 are unused, since QUUX has no second boot and no no-auto-boot, and %s1 resets the machine; '
              '%s0 shows the machine running, not halted, and %s5 is dark, since QUUX has no PROM select%s. '
              'Every block this project builds is done and drawn green; the parts drawn gray are components of the board. '
              % (btn, btn, lamp, lamp, '' if arty else '; LEDR6, under them, is lit while the memory port is open'))

def quux_svg(board):
    arty = board == 'arty-z7-20'
    kria = board == 'kria-kr260'
    zynq = arty or kria
    gp0, gp1 = QUUX_PORTS[board]
    clk_in, pll, top = QUUX_CLOCK[board]
    base = board_svg('arty-z7-20.html')
    base, n = re.subn(r'\n[ \t]*<!--.*?-->[ \t]*(?=\n)', '', base, flags=re.S)
    assert '<!--' not in base
    # the head: the key, the outline, the chip, the display output and its port, the HDMI box
    i = base.index('          <text class="d-s" x="-164" y="48">Programmable Logic</text>\n')
    head = base[:i]
    i2 = base.index('          <path class="d-dash" d="M-170,450 L-150,450')
    tail = base[i2:]
    tail = sub(tail, mem_block('arty'), mem_block('arty', True, True))
    # (1) head
    head = re.sub(r'aria-label="[^"]*"', 'aria-label="%s"' % quux_aria(board), head, count=1)
    head = sub(head, '''          <text class="d-s" x="-70" y="318" text-anchor="middle">scans both screens out of</text>
          <text class="d-s" x="-70" y="332" text-anchor="middle">DDR at the monitor&rsquo;s rate,</text>
          <text class="d-s" x="-70" y="346" text-anchor="middle">side by side, the color one</text>
          <text class="d-s" x="-70" y="360" text-anchor="middle">over the first; TMDS to HDMI</text>
''', '''          <text class="d-s" x="-70" y="318" text-anchor="middle">scans the frame buffer</text>
          <text class="d-s" x="-70" y="332" text-anchor="middle">out of DDR at the</text>
          <text class="d-s" x="-70" y="346" text-anchor="middle">monitor&rsquo;s rate;</text>
          <text class="d-s" x="-70" y="360" text-anchor="middle">TMDS to HDMI</text>
''' if not kria else '''          <text class="d-s" x="-70" y="318" text-anchor="middle">scans the frame buffer</text>
          <text class="d-s" x="-70" y="332" text-anchor="middle">out of DDR at the</text>
          <text class="d-s" x="-70" y="346" text-anchor="middle">monitor&rsquo;s rate, and hands</text>
          <text class="d-s" x="-70" y="360" text-anchor="middle">it to the DisplayPort</text>
          <text class="d-s" x="-70" y="374" text-anchor="middle">controller</text>
''')
    head = sub(head, '          <path class="d-line" d="M470,274 L470,256 L-70,256 L-70,274"/>\n', '')
    # (2) the fabric
    # the bars, a third for the Kria KR260's UltraRAM, and the slack under the last
    f = F.fit(board, 'quux')
    bars = F.fit_rows(f)
    slack, down = F.setup(f), 36 * (len(bars) - 2)
    fabric = ('          <text class="d-s" x="-164" y="48">%s</text>\n' % ('Programmable Logic' if zynq else 'FPGA fabric logic')
              + fit_bars(bars) + slack_block(slack, 140 + down) + '\n')
    if kria:
        fabric += '''          <text class="d-s" x="-164" y="%d">adapters in the fabric</text>
          <text class="d-s" x="-164" y="%d">meet every port at</text>
          <text class="d-s" x="-164" y="%d">128 bits</text>
''' % (170 + down, 184 + down, 198 + down)
    fabric += '''          <rect class="d-box d-done" x="940" y="62" width="112" height="128"/>
          <text class="d-t" x="996" y="100" text-anchor="middle">clock</text>
          <text class="d-n" x="996" y="120" text-anchor="middle">%s</text>
          <text class="d-s" x="996" y="138" text-anchor="middle">%s</text>
          <text class="d-s" x="996" y="152" text-anchor="middle">%s</text>
          <text class="d-s" x="996" y="166" text-anchor="middle">period %s ns,</text>
          <text class="d-s" x="996" y="180" text-anchor="middle">a stage a clock</text>

          <rect class="d-box d-done" x="40" y="62" width="224" height="84"/>
          <text class="d-t" x="152" y="84" text-anchor="middle">processor</text>
          <text class="d-s" x="152" y="102" text-anchor="middle">32-bit word, MUL and DIV,</text>
          <text class="d-s" x="152" y="116" text-anchor="middle">control store 16K &times; 48,</text>
          <text class="d-s" x="152" y="130" text-anchor="middle">PDL buffer 16K words</text>
          <rect class="d-box d-done" x="40" y="146" width="224" height="44"/>
          <text class="d-t" x="152" y="164" text-anchor="middle">the map</text>
          <text class="d-s" x="152" y="178" text-anchor="middle">two levels, 2,048 in the second</text>

          <rect class="d-box d-done" x="290" y="62" width="150" height="128"/>
          <text class="d-t" x="365" y="84" text-anchor="middle">memory port</text>
          <text class="d-s" x="365" y="104" text-anchor="middle">one requester;</text>
          <text class="d-s" x="365" y="118" text-anchor="middle">a cycle goes to</text>
          <text class="d-s" x="365" y="132" text-anchor="middle">the memory bus,</text>
          <text class="d-s" x="365" y="146" text-anchor="middle">a device register</text>
          <text class="d-s" x="365" y="160" text-anchor="middle">or nowhere</text>
          <rect class="d-box d-done" x="470" y="62" width="150" height="128"/>
          <text class="d-t" x="545" y="84" text-anchor="middle">cache</text>
          <text class="d-s" x="545" y="104" text-anchor="middle">4,096 words,</text>
          <text class="d-s" x="545" y="118" text-anchor="middle">two ways,</text>
          <text class="d-s" x="545" y="132" text-anchor="middle">write-through,</text>
          <text class="d-s" x="545" y="146" text-anchor="middle">lines of 4 words</text>
          <line class="d-line" x1="264" y1="104" x2="290" y2="104"/>
          <line class="d-line" x1="440" y1="126" x2="470" y2="126"/>
          <path class="d-line" d="M365,62 L365,46 L777,46 L777,62"/>
          <text class="d-s" x="571" y="40" text-anchor="middle">device cycles</text>

          <rect class="d-box d-done" x="650" y="62" width="254" height="128"/>
          <text class="d-t" x="777" y="84" text-anchor="middle">register page</text>
          <text class="d-n" x="777" y="102" text-anchor="middle">17777400 to 17777777</text>
          <text class="d-s" x="777" y="122" text-anchor="middle">the feature words, read only;</text>
          <text class="d-s" x="777" y="136" text-anchor="middle">the interrupt status, errors,</text>
          <text class="d-s" x="777" y="150" text-anchor="middle">three interval timers and</text>
          <text class="d-s" x="777" y="164" text-anchor="middle">the real-time clock</text>

          <rect class="d-box d-done" x="1068" y="96" width="188" height="64"/>
          <text class="d-t" x="1162" y="118" text-anchor="middle">console</text>
          <text class="d-s" x="1162" y="138" text-anchor="middle">boot, halt, step, status</text>
          <text class="d-s" x="1162" y="152" text-anchor="middle">the registers on %s</text>
          <path class="d-line" d="M1162,160 L1162,428"/>

          <path class="d-line" d="M545,190 L545,214 L118,214 L118,274"/>
          <path class="d-line" d="M777,190 L777,238"/>
          <line class="d-bus" x1="310" y1="238" x2="885" y2="238"/>
          <text class="d-s" x="310" y="228">device registers</text>
          <path class="d-line" d="M310,238 L310,274 M497,238 L497,274 M657,238 L657,274 M885,238 L885,274"/>

          <rect class="d-box d-done" x="40" y="274" width="156" height="112"/>
          <text class="d-t" x="118" y="300" text-anchor="middle">memory master</text>
          <text class="d-s" x="118" y="320" text-anchor="middle">lines of 4 words in</text>
          <text class="d-s" x="118" y="334" text-anchor="middle">two 64-bit beats</text>
          <text class="d-n" x="118" y="356" text-anchor="middle">quux_axi_master</text>
          <text class="d-s" x="118" y="376" text-anchor="middle">an AXI4 master</text>

          <rect class="d-box d-done" x="210" y="274" width="200" height="112"/>
          <text class="d-t" x="310" y="300" text-anchor="middle">block-disk</text>
          <text class="d-s" x="310" y="320" text-anchor="middle">four registers, 200 to 203;</text>
          <text class="d-s" x="310" y="334" text-anchor="middle">blocks to and from a pack</text>
          <text class="d-n" x="310" y="356" text-anchor="middle">quux_block_disk</text>
          <text class="d-s" x="310" y="376" text-anchor="middle">the pack side, a master</text>

          <rect class="d-box d-done" x="424" y="274" width="146" height="112"/>
          <text class="d-t" x="497" y="300" text-anchor="middle">video controller</text>
          <text class="d-s" x="497" y="320" text-anchor="middle">one-bit frame buffer,</text>
          <text class="d-s" x="497" y="334" text-anchor="middle">1280 &times; 1024, a mode</text>
          <text class="d-n" x="497" y="356" text-anchor="middle">quux_video</text>
          <text class="d-s" x="497" y="376" text-anchor="middle">the buffer is in DDR</text>

          <rect class="d-box d-done" x="584" y="274" width="146" height="112"/>
          <text class="d-t" x="657" y="300" text-anchor="middle">file device</text>
          <text class="d-s" x="657" y="320" text-anchor="middle">two rings in main</text>
          <text class="d-s" x="657" y="334" text-anchor="middle">memory; registers</text>
          <text class="d-n" x="657" y="356" text-anchor="middle">quux_file_device</text>
          <text class="d-s" x="657" y="376" text-anchor="middle">its host face on %s</text>

          <rect class="d-box d-done" x="780" y="274" width="210" height="112"/>
          <text class="d-t" x="885" y="300" text-anchor="middle">keyboard and mouse</text>
          <text class="d-s" x="885" y="320" text-anchor="middle">a FIFO of 64 key words,</text>
          <text class="d-s" x="885" y="334" text-anchor="middle">the mouse&rsquo;s counts, buttons</text>
          <text class="d-n" x="885" y="356" text-anchor="middle">quux_input</text>
          <text class="d-s" x="885" y="376" text-anchor="middle">the cable, not the protocol</text>

          <path class="d-line" d="M118,386 L118,428 M310,386 L310,428 M657,386 L657,428 M885,386 L885,428"/>

''' % (top, clk_in, pll, F.period(board), gp1, gp0)
    # (3) the tail: the programs, the memory, no Pmod
    tail = sub(tail, '''          <path class="d-line" d="M845,466 L845,494 M305,494 L1040,494 M305,494 L305,542 M452,494 L452,542 M599,494 L599,542 M746,494 L746,542 M893,494 L893,542 M1040,494 L1040,542"/>''',
               '''          <path class="d-line" d="M845,466 L845,494 M452,494 L1040,494 M452,494 L452,542 M599,494 L599,542 M746,494 L746,542 M893,494 L893,542 M1040,494 L1040,542"/>''')
    # the six program slots: the first is empty, the file device takes the third
    def prog(x, title, lines):
        out = ('          <rect class="d-plate" x="%d" y="542" width="130" height="96"/>\n'
               '          <rect class="d-box d-done" x="%d" y="542" width="130" height="96"/>\n'
               '          <text class="d-t" x="%d" y="566" text-anchor="middle">%s</text>\n' % (x, x, x + 65, title))
        for y, s in lines:
            out += '          <text class="d-s" x="%d" y="%d" text-anchor="middle">%s</text>\n' % (x + 65, y, s)
        return out
    a = tail.index('          <rect class="d-plate" x="240" y="542" width="130" height="96"/>')
    b = tail.index('          <path class="d-line" d="M118,466 L118,652"/>')
    tail = tail[:a] + (
        prog(387, 'terminal', [(586, 'an RFB server: the screen,'), (600, 'the keys and the mouse')])
        + prog(534, 'file device', [(586, 'serves HOST and'), (600, 'sets the clock,'), (614, 'from the card')])
        + prog(681, 'disk packs', [(586, 'a drive&rsquo;s blocks as a file,'), (600, 'one file a drive'), (622, 'staged into DDR')])
        + prog(828, 'console', [(586, 'halt, step and inspect'), (600, 'over %s' % ('M_AXI_GP1' if arty else gp1)), (622, 'the registers')])
        + prog(975, 'USB input', [(586, 'the keyboard and'), (600, 'mouse, onto the'), (614, 'register page'), (628, 'via the terminal')])
        + '\n') + tail[b:]
    # Arty's lines from the program boxes to the controllers: the terminal to the MAC,
    # the file device to the SD host with a jog, the packs to the SD host, the console to the
    # UART, the USB input to the USB host
    tail = sub(tail, '''          <path class="d-line" d="M305,638 L305,652 M452,638 L452,652 M599,638 L599,652 M746,638 L746,652"/>''',
               '''          <path class="d-line" d="M452,638 L452,652 M599,638 L599,645 L700,645 L700,652 M746,638 L746,652"/>''')
    # no Pmod
    a = tail.index('          <rect class="d-box d-ext" x="1366" y="88" width="150" height="98"/>')
    b = tail.index('          <rect class="d-box d-ext" x="1366" y="264" width="150" height="66"/>')
    tail = tail[:a] + tail[b:]
    tail = sub(tail, '          <path class="d-line" d="M1256,120 L1366,120"/>\n', '') if '<path class="d-line" d="M1256,120 L1366,120"/>' in tail else tail
    tail = sub(tail, '<text class="d-s" x="746" y="758" text-anchor="middle">U-Boot, the CADR&rsquo;s bitstream,</text>',
               '<text class="d-s" x="746" y="758" text-anchor="middle">U-Boot, the bitstream,</text>')
    tail = sub(tail, '''          <text class="d-s" x="453" y="762" text-anchor="middle">the terminal is a VNC client; Chaosnet reaches</text>
          <text class="d-s" x="453" y="778" text-anchor="middle">other machines; the serial line is a TCP socket</text>
''', '''          <text class="d-s" x="453" y="768" text-anchor="middle">the terminal is a VNC client</text>
''')
    svg = head + fabric + tail
    # revision 15, on every board: revision 13's word, control store, PDL
    # buffer, register page and lines, revision 14's map, revision 15's
    # modules and the board's cache
    svg = sub(svg, '>32-bit word, MUL and DIV,<', '>40-bit word, MUL and DIV,<')
    svg = sub(svg, '>control store 16K &times; 48,<', '>control store 16K words,<')
    svg = sub(svg, '>the map<', '>the TLB<')
    svg = sub(svg, '>two levels, 2,048 in the second<', '>4,096 entries, a walk on a miss<')
    svg = sub(svg, '>4,096 words,<', '>%s words,<' % F.cache_words(board))
    svg = sub(svg, '>lines of 4 words<', '>lines of 8 words<')
    for old, new in (('quux_axi_master', 'quux15_axi_master'), ('quux_block_disk', 'quux15_block_walk'),
                     ('quux_video', 'quux15_devices'), ('quux_file_device', 'quux15_devices'),
                     ('quux_input', 'quux15_input')):
        svg = sub(svg, '>%s<' % old, '>%s<' % new)
    svg = sub(svg, '>17777400 to 17777777<', '>physical 1777777400-1777777777<')
    svg = sub(svg, '>lines of 4 words in<', '>lines of 8 words in<')
    svg = sub(svg, '>two 64-bit beats<', '>five 64-bit beats<')
    # block-disk's transfer is a second requester of the port, below the processor (quux15_port.sv's D), so the box does not count them
    svg = sub(svg, '''          <text class="d-s" x="365" y="104" text-anchor="middle">one requester;</text>
          <text class="d-s" x="365" y="118" text-anchor="middle">a cycle goes to</text>
          <text class="d-s" x="365" y="132" text-anchor="middle">the memory bus,</text>
          <text class="d-s" x="365" y="146" text-anchor="middle">a device register</text>
          <text class="d-s" x="365" y="160" text-anchor="middle">or nowhere</text>
''', '''          <text class="d-s" x="365" y="104" text-anchor="middle">a cycle goes to</text>
          <text class="d-s" x="365" y="118" text-anchor="middle">the memory bus,</text>
          <text class="d-s" x="365" y="132" text-anchor="middle">a device register</text>
          <text class="d-s" x="365" y="146" text-anchor="middle">or nowhere</text>
''')
    if board == 'de25-nano':
        svg = quux_de25(svg)
    elif kria:
        svg = quux_kria(svg)
    if not kria:
        svg = sub(svg, '>1280 &times; 1024, a mode<', '>%s, a mode<' % F.display(board, ' &times; '))
    if not kria:
        # the buttons, the switch and the lamps, where revision 15 has the
        # signal (docs/board.md at bbd7f1a, "The buttons", "The switches",
        # "What the LEDs say"): no second boot, no no-auto-boot, no MACHRUN
        # and no PROM select
        btn, lamp = ('BTN', 'LD') if board == 'arty-z7-20' else ('KEY', 'LEDR')
        svg = sub(svg, '>%s0 &mdash; BOOT<' % btn, '>%s0 &mdash; unused<' % btn)
        svg = sub(svg, '>SW0 &mdash; NO AUTO BOOT<', '>SW0 &mdash; unused<')
        svg = sub(svg, '>%s0 &mdash; MACHRUN<' % lamp, '>%s0 &mdash; running<' % lamp)
        svg = sub(svg, '>%s5 &mdash; PROMENABLE<' % lamp, '>%s5 &mdash; dark<' % lamp)
        # the dark lamp is drawn unlit
        dark = re.findall(r'<circle cx="1380" cy="466" r="4.5" fill="#[0-9a-f]{6}" fill-opacity="1"', svg)
        assert len(dark) == 1, dark
        svg = sub(svg, dark[0], '<circle cx="1380" cy="466" r="4.5" fill="none" fill-opacity="1"')
    if board == 'de25-nano':
        # LEDR6, lit while the memory port is open (quux15_de25.sv's header,
        # "THE LAMPS", and its `led` row, at bbd7f1a): a seventh lamp under
        # the six, green as every LEDR is, the box one lamp taller.  The Arty
        # Z7-20 has six lamps and the Kria KR260 two, and neither top lights
        # one for the port.
        svg = sub(svg, '<rect class="d-box d-ext" x="1366" y="336" width="150" height="152"/>',
                  '<rect class="d-box d-ext" x="1366" y="336" width="150" height="174"/>')
        svg = sub(svg, '          <text class="d-s" x="1394" y="470">LEDR5 &mdash; dark</text>\n',
                  '          <text class="d-s" x="1394" y="470">LEDR5 &mdash; dark</text>\n'
                  '          <circle cx="1380" cy="488" r="4.5" fill="#2da44e" fill-opacity="1" stroke="currentColor" stroke-width="1"/>\n'
                  '          <text class="d-s" x="1394" y="492">LEDR6 &mdash; memory port open</text>\n')
    return svg

def quux_kria(svg):
    """The Arty-based QUUX drawing, for the Kria KR260 at revision 15: the
    changes kr260_svg() makes to the CADR's, to the blocks the two drawings
    share (the kria_* functions), and the Kria KR260's own: its part, and
    the master's bursts narrowed onto the 128-bit port; quux_svg() makes
    the changes every board's revision 15 shares, the clock and the cache
    the board's.  Read from muir-fpga's boards/kria-kr260/quux15_kr260.sv at
    bbd7f1a, rtl/plumbing/quux_axi_narrow128.sv and docs/linux.md."""
    svg = kria_loader(svg)
    svg = sub(svg, '<text class="d-s" x="-164" y="24">AMD Zynq 7020 &middot; XC7Z020-1CLG400C</text>',
              '<text class="d-s" x="-164" y="24">%s &middot; %s</text>' % (KR260_PART[1], KR260_PART[0]))
    svg = kria_display(svg)
    svg = kria_ports(svg)
    svg = sub(svg, '>an AXI4 master<', '>on the 128-bit port<')
    svg = sub(svg, '>1280 &times; 1024, a mode<', '>a mode<')
    svg = kria_ps(svg, ('the bitstream,', 'bitstream,'))
    svg = sub(svg, mem_block('arty', True, True), mem_block('kria', True, True))
    svg = kria_right(svg)
    svg = kria_border(svg)
    return svg

def quux_de25(svg):
    """The Arty-based QUUX drawing, for the DE25-Nano: the same changes
    de25_svg() makes to the CADR's, to the blocks the two drawings share."""
    svg = sub(svg, '<text class="d-s" x="-164" y="24">AMD Zynq 7020 &middot; XC7Z020-1CLG400C</text>',
              '<text class="d-s" x="-164" y="24">%s &middot; %s</text>' % (DE25_PART[1], DE25_PART[0]))
    svg = sub(svg, mem_block('arty', True, True), mem_block('de25', True, True))
    svg = sub(svg, '<text class="d-t" x="87" y="738" text-anchor="middle">512 MB DDR3</text>',
              '<text class="d-t" x="87" y="738" text-anchor="middle">1 GB LPDDR4</text>')
    lamps = re.findall(r'<circle [^>]*cx="1380"[^>]*/>', svg)
    assert len(lamps) == 8, len(lamps)
    for c in lamps:
        svg = sub(svg, c, re.sub(r'(fill|stroke)="#(?:d1495b|0969da)"', r'\1="#2da44e"', c))
    svg = sub(svg, 'text-anchor="middle">PL masters, 64 bits, AXI3</text>', 'text-anchor="middle">FPGA masters, 64 bits, AXI3</text>', 3)
    svg = sub(svg, 'text-anchor="middle">PS masters, 32 bits, AXI3</text>', 'text-anchor="middle">HPS masters, AXI4</text>', 2)
    svg = sub(svg, '<text class="d-s" x="-164" y="520.4">PS &mdash; Arm</text>', '<text class="d-s" x="-164" y="520.4">HPS &mdash; Arm</text>')
    svg = sub(svg, '''          <text class="d-t" x="-7" y="566" text-anchor="middle">2 &times; Cortex-A9</text>
          <text class="d-s" x="-7" y="586" text-anchor="middle">650 MHz, Linux</text>
''', '''          <text class="d-t" x="-7" y="560" text-anchor="middle">2 &times; Cortex-A76</text>
          <text class="d-s" x="-7" y="574" text-anchor="middle">up to 1.4 GHz</text>
          <text class="d-t" x="-7" y="594" text-anchor="middle">2 &times; Cortex-A55</text>
          <text class="d-s" x="-7" y="608" text-anchor="middle">up to 1.25 GHz</text>
          <text class="d-s" x="-7" y="628" text-anchor="middle">Linux</text>
''')
    # the one memory port, F2SDRAM, in the place of the three HP boxes
    svg = sub(svg, '''          <rect class="d-plate" x="-150" y="428" width="160" height="38"/>
          <rect class="d-box d-done" x="-150" y="428" width="160" height="38"/>
          <text class="d-m" x="-70" y="446" text-anchor="middle">S_AXI_HP3</text>
          <text class="d-s" x="-70" y="460" text-anchor="middle">FPGA masters, 64 bits, AXI3</text>
''', '''          <rect class="d-plate" x="-150" y="428" width="540" height="38"/>
          <rect class="d-box d-done" x="-150" y="428" width="540" height="38"/>
          <text class="d-m" x="120" y="446" text-anchor="middle">F2SDRAM</text>
          <text class="d-s" x="120" y="460" text-anchor="middle">fabric masters, 64 bits, AXI4, one port shared by burst</text>
''')
    svg = sub(svg, '''          <rect class="d-plate" x="38" y="428" width="160" height="38"/>
          <rect class="d-box d-done" x="38" y="428" width="160" height="38"/>
          <text class="d-m" x="118" y="446" text-anchor="middle">S_AXI_HP0</text>
          <text class="d-s" x="118" y="460" text-anchor="middle">FPGA masters, 64 bits, AXI3</text>
''', '')
    svg = sub(svg, '''          <rect class="d-box d-done" x="230" y="428" width="160" height="38"/>
          <text class="d-m" x="310" y="446" text-anchor="middle">S_AXI_HP2</text>
          <text class="d-s" x="310" y="460" text-anchor="middle">FPGA masters, 64 bits, AXI3</text>
''', '')
    svg = sub(svg, '<path class="d-line" d="M-70,466 L-70,652"/>', '<path class="d-line" d="M120,466 L120,652"/>')
    svg = sub(svg, '          <path class="d-line" d="M118,466 L118,652"/>\n', '')
    svg = sub(svg, '          <path class="d-line" d="M240,466 L240,494 L170,494 L170,652"/>\n', '')
    svg = sub(svg, '<path class="d-dash" d="M-170,450 L-150,450 M10,450 L38,450 M198,450 L230,450 M390,450 L640,450 M1050,450 L1092,450 M1232,450 L1351,450"/>',
              '<path class="d-dash" d="M-170,450 L-150,450 M390,450 L640,450 M1050,450 L1092,450 M1232,450 L1351,450"/>')
    svg = sub(svg, '<text class="d-m" x="845" y="446" text-anchor="middle">M_AXI_GP0</text>', '<text class="d-m" x="845" y="446" text-anchor="middle">H2F</text>')
    svg = sub(svg, '<text class="d-m" x="1162" y="446" text-anchor="middle">M_AXI_GP1</text>', '<text class="d-m" x="1162" y="446" text-anchor="middle">LWH2F</text>')
    svg = sub(svg, 'over the first; TMDS to HDMI</text>', 'over the first; to the ADV7513</text>') if 'over the first; TMDS to HDMI' in svg else sub(svg, '<text class="d-s" x="-70" y="360" text-anchor="middle">TMDS to HDMI</text>', '<text class="d-s" x="-70" y="360" text-anchor="middle">to the ADV7513</text>')
    svg = sub(svg, '          <text class="d-s" x="87" y="684" text-anchor="middle">four ports, arbitrated in hardware</text>\n', '')
    svg = sub(svg, '>BTN0 &mdash; BOOT</text>', '>KEY0 &mdash; BOOT</text>')
    svg = sub(svg, '>BTN1 &mdash; RESET</text>', '>KEY1 &mdash; RESET</text>')
    for n in range(6):
        svg = sub(svg, '>LD%d &mdash; ' % n, '>LEDR%d &mdash; ' % n)
    svg = sub(svg, '''          <text class="d-t" x="897" y="738" text-anchor="middle">USB-UART</text>
          <text class="d-t" x="897" y="756" text-anchor="middle">/ JTAG</text>
          <text class="d-s" x="897" y="778" text-anchor="middle">one micro-USB socket,</text>''',
              '''          <text class="d-t" x="897" y="738" text-anchor="middle">USB-Blaster III</text>
          <text class="d-s" x="897" y="778" text-anchor="middle">one USB-C socket,</text>''')
    return svg


DESC = {}
for _f in ('arty-z7-20.html',):
    DESC[_f] = re.search(r'<meta name="description" content="([^"]*)">', open(os.path.join(BASE, _f)).read()).group(1)
# The board runs the design, so it is not "proposed".
DESC['arty-z7-20.html'] = sub(DESC['arty-z7-20.html'], 'The proposed architecture for running the MIT CADR Lisp Machine in fabric',
                              'The MIT CADR Lisp Machine in fabric')

# ================================================================ booting

def build_booting():
    base = open(os.path.join(BASE, 'booting.html')).read()
    comment = re.search(r'<!-- THE SEQUENCES CARRY NO COLOR OF THE BOARD DRAWINGS.*?-->', base, re.S).group(0)
    s1, s2, s3, s4 = svgs('booting.html')
    # What the board said in its speech bubbles is said here in plain
    # sentences, in the third person.
    P = [comment, '\n']
    P.append(hero('muir-fpga &middot; booting', 'How a board<br>comes <em>up.</em>',
                  'Four sequences, two for the Arty Z7-20 and two for the DE25-Nano: from the board&rsquo;s own card, which is how anybody else&rsquo;s board boots, and with TFTP, which is how this project&rsquo;s own boards boot while they are being worked on.',
                  body='<div class="hero-description">\n'
                       '<p>The Arty Z7-20 is a Zynq-7000 board, and its two sequences are the first two below.</p>\n'
                       '<p>The DE25-Nano has a pair of its own, because it boots differently enough to need one. Its boot crosses two storage devices rather than one, and its fabric is configured in the middle of the sequence rather than by the loader&rsquo;s first stage.</p>\n'
                       '<p>On either board the two paths differ only in where the files come from. The loader itself is read the same way on both, and the same last step ends both.</p>\n'
                       '<p>The Kria KR260 boots by its own loader, in its flash, which this project leaves alone: it reads the card, which it sees as a USB disk, or a server on the network, and loads Linux and then the bitstream from there (<a href="kria-kr260.html">its page</a>).</p>\n'
                       '</div>\n'))

    P.append(section('card', '01 / A ZYNQ-7000 BOARD, FROM ITS CARD', 'A Zynq-7000 board<br>on <em>its own.</em>',
        'This is how a board boots for anybody who is not this project: the loader, the CADR&rsquo;s bitstream, Linux with its root filesystem, and the disk packs are all on the microSD card.',
        '''<div class="cols">
<div>
<p class="lead">The card&rsquo;s one partition. The four files the loader reads next sit in a folder named for the board, as they do on the server:</p>
<pre>BOOT.BIN      <b>fixed name</b>  the boot ROM reads it here and nowhere else
u-boot.img    <b>fixed name</b>  the first stage asks for it by this name
uEnv.txt      <b>fixed name</b>  imported before any board name is known
&lt;board&gt;/     cadr.bit, the tree, zImage, rootfs.cpio.uboot</pre>
</div>
<p class="callout">Everything the board needs is on its card. No network is used and none is needed.</p>
</div>
''' + figure(s1, 'The card holds everything, the CADR is in the fabric before the kernel is fetched, and the machine&rsquo;s own boot PROM waits in its no-drive loop until Linux presents it a disk. The Arty Z7-20 has booted this way with no network at all.',
             cls='fig dense', label='FIG. 01 &mdash; A ZYNQ-7000 BOARD, FROM ITS CARD', name='A Zynq-7000 board, from its card')))

    # THE DEVELOPMENT PATH IS NAMED FOR WHAT IT USES, on both boards and in the
    # same words: "with TFTP", and the parenthetical says what it is for.  The
    # two paths are then told apart by the thing that differs between them --- a
    # card or a server --- rather than by who happens to be using each.
    P.append(section('server', '02 / A ZYNQ-7000 BOARD, FOR DEVELOPMENT', 'A Zynq-7000 board<br>with <em>TFTP.</em>',
        'This project&rsquo;s own boards take the same five files from a TFTP server instead.',
        '''<div class="cols">
<p class="callout">A change to any of the board&rsquo;s five files is a copy on the server and a reset. Its card is never rewritten.</p>
<div class="prose"><p>The card&rsquo;s <code>uEnv.txt</code> decides between the two paths, by whether it names a server, and one U-Boot environment carries both. Each board&rsquo;s five files sit in a directory named for the board, and the network path never falls back to the card&rsquo;s own copies.</p></div>
</div>
''' + figure(s2, 'The two paths differ only in where the bytes come from: both put the CADR in the fabric before the kernel, and both end in the same <code>bootz</code>.',
             cls='fig dense', label='FIG. 02 &mdash; A ZYNQ-7000 BOARD, WITH TFTP', name='A Zynq-7000 board, with TFTP')))

    # THE DE25-NANO, a third sequence rather than a variant of either above.
    # Two things separate it and the drawing is here to show both: the boot
    # crosses a flash AND a card, where a Zynq board's crosses one card; and
    # the fabric is configured in the middle of the sequence, by the
    # second-stage loader, where a Zynq board's is configured before the
    # kernel is fetched by a loader that was itself already running from the
    # same card.  The order inside the fabric's turn is the detail that
    # matters and it is the environment's own: the bridges are released
    # BEFORE the gate is raised, and the kernel is fetched only after both.
    P.append(section('de25', '03 / THE DE25-NANO, FROM ITS CARD', 'The DE25-Nano<br>on <em>its own.</em>',
        'This board takes the same two paths as the Arty Z7-20, and reaches them differently. There is no <code>BOOT.BIN</code>, because the first-stage loader is in the QSPI flash; and the fabric is empty until U-Boot fills it.',
        '''<div class="cols">
<div>
<p class="lead">The card&rsquo;s one partition. Two names are not this project&rsquo;s to move, and the rest sit in a folder named for the board:</p>
<pre>u-boot.itb    <b>fixed name</b>  the first stage asks for it by this name
uEnv.txt      <b>fixed name</b>  imported before any board name is known
de25-nano/    cadr.core.rbf, the tree, Image, rootfs.cpio.uboot</pre>
</div>
<p class="callout">The board&rsquo;s first phase is in the flash and everything after it is on the card. Its fabric is filled by the loader, not before it.</p>
</div>
''' + figure(s3, 'The four steps of the fabric&rsquo;s turn are in the order the boot environment runs them: the image is read, the gate is shut, the CADR is configured, the bridges are released, and only then is the gate opened. The kernel is fetched after all four, so the machine&rsquo;s first memory cycle cannot meet a bridge still in reset.',
             cls='fig dense', label='FIG. 03 &mdash; THE DE25-NANO, FROM ITS CARD', name='The DE25-Nano, from its card')))

    # THE DE25-NANO WITH TFTP, the fourth sequence.  What it is here to show is
    # how little the network changes on this board: the QSPI flash holds the
    # phase-1 bitstream and no CADR, and that step does not move; u-boot.itb and
    # uEnv.txt are read off the card on this path too, because the first stage
    # asks for u-boot.itb by name at the root and U-Boot imports uEnv.txt before
    # any board name is known, so neither can come from a server; and the four
    # steps of the fabric's turn are the card path's own, with only the fetch
    # before them changed.  What the network adds is the dhcp, the second import
    # of the card's uEnv.txt (so a lease cannot displace the server the card
    # named), and the served uEnv.net.  IT HAS RUN ON THE BOARD, on 22 September
    # 2026, and the section lede, the drawing's byte counts and the times down
    # its left are that one run's, as the Zynq drawing's and the DE25 card
    # drawing's are of theirs.  The session is docs/board.md, "The DE25-Nano
    # over TFTP".
    P.append(section('de25-server', '04 / THE DE25-NANO, FOR DEVELOPMENT', 'The DE25-Nano<br>with <em>TFTP.</em>',
        'A change to any of the five served files is then a copy and a reset, and the card is never rewritten. This path has run on the board: 48,691,884 bytes over the network, and 28 seconds from the reset to the login prompt, against 25 off the card.',
        '''<div class="cols">
<p class="callout">The board&rsquo;s flash and card still carry its loader. Only the five files after it come from the server.</p>
<div class="prose"><p>The first-stage loader is in the QSPI flash, and it asks for <code>u-boot.itb</code> by that name at the root of the card, so neither of them comes from the server: the first stage reads the card, and it is U-Boot that speaks TFTP here. <code>uEnv.txt</code> is read off the card on this path too, and it is the file that chose the path. The four steps of the fabric&rsquo;s turn are the card path&rsquo;s own, and only the fetch before them changes.</p></div>
</div>
''' + figure(s4, 'The same board, the same flash and the same card, with a server in the middle. What the network changes is where the five files come from, and nothing else: the loader is still read off the card, and the boot ends in the same <code>booti</code>.',
             cls='fig dense', label='FIG. 04 &mdash; THE DE25-NANO, WITH TFTP', name='The DE25-Nano, with TFTP'),
        label='The DE25-Nano with TFTP, used for development'))
    page('booting.html', 'muir-fpga &mdash; booting',
         'How each board here comes up, in four sequences: a Zynq-7000 board and the DE25-Nano, each from its own microSD card, and each with TFTP while it is being worked on.',
         P)

# ============================================== the debug cable on the Pmod boards

# The twelve pins of a Pmod, what each carries, and each board's package pin,
# from the Arty Z7-20's .xdc (Digilent's file) and the Kria KR260's PMOD1 section of
# muir-fpga's docs/debug-cable.md and boards/kria-kr260/cadr_kr260.xdc (AMD's
# board files).  A ribbon between any two of these Pmods joins pin n to pin n
# (straight) or to the other row's pin (mirrored).
PMOD_BOARDS = (('arty', 'Arty JA'), ('kria', 'Kria PMOD1'))
PMOD_PINS = {
    1: ('debugger strobe', {'arty': 'Y18', 'kria': 'H12'}),
    2: ('guard, driven low', {'arty': 'Y19', 'kria': 'E10'}),
    3: ('debugger data', {'arty': 'Y16', 'kria': 'D10'}),
    4: ('guard, driven low', {'arty': 'Y17', 'kria': 'C11'}),
    5: ('ground', None), 6: ('3.3 V', None),
    7: ('debuggee strobe', {'arty': 'U18', 'kria': 'B10'}),
    8: ('guard, driven low', {'arty': 'U19', 'kria': 'E12'}),
    9: ('debuggee data', {'arty': 'W18', 'kria': 'D11'}),
    10: ('guard, driven low', {'arty': 'W19', 'kria': 'B11'}),
    11: ('ground', None), 12: ('3.3 V', None),
}

def pmod_cable_svg(boards=('arty', 'kria')):
    """The Pmod's twelve pins: for each, what it carries, the package pin on
    each board in `boards`, and the pin it meets at the far Pmod on a straight
    ribbon and on a mirrored one."""
    names = dict(PMOD_BOARDS)
    nb = len(boards)
    cw, x0 = 160, 50
    sig_h = 118 + 16 * nb      # pin, role, one line a board, straight, mirrored
    ch = sig_h
    ys = (84, 84 + ch + 24)
    out = []
    onboards = ' and '.join(names[b] for b in boards) if nb < 2 else 'the Arty Z7-20&rsquo;s JA and the Kria KR260&rsquo;s PMOD1'
    aria = ('The debug cable on a Pmod, drawn as its twelve pins in two rows, pins 1 to 6 above and 7 to 12 below. '
            'For each pin, what it carries, its package pin on %s, and the pin of the far Pmod that it meets on a straight ribbon and on a mirrored one. ') % (
            'the Kria KR260&rsquo;s PMOD1' if boards == ('kria',) else onboards)
    for n in range(1, 13):
        role, pads = PMOD_PINS[n]
        x, y = x0 + ((n - 1) % 6) * cw, ys[(n - 1) // 6]
        cx = x + cw // 2
        straight = n
        mirrored = n + 6 if n <= 6 else n - 6
        supply = role == '3.3 V'
        cls = 'd-absent' if supply else 'd-box'
        if role == 'ground':
            out.append('          <rect class="d-tint" x="%d" y="%d" width="%d" height="%d"/>' % (x, y, cw, ch))
        out.append('          <rect class="%s" x="%d" y="%d" width="%d" height="%d"/>' % (cls, x, y, cw, ch))
        out.append('          <text class="d-t" x="%d" y="%d" text-anchor="middle">pin %d</text>' % (cx, y + 24, n))
        out.append('          <text class="d-x" x="%d" y="%d" text-anchor="middle">%s</text>' % (cx, y + 42, role))
        out.append('          <path class="d-line" d="M%d,%d H%d" stroke-opacity="0.3"/>' % (x + 10, y + 52, x + cw - 10))
        if pads:
            for i, b in enumerate(boards):
                ly = y + 70 + 16 * i
                out.append('          <text class="d-x" x="%d" y="%d">%s</text>' % (x + 12, ly, names[b]))
                out.append('          <text class="d-s" x="%d" y="%d" text-anchor="end">%s</text>' % (x + cw - 12, ly, pads[b]))
        else:
            out.append('          <text class="d-x" x="%d" y="%d" text-anchor="middle">no package pin</text>' % (cx, y + 70))
        ry = y + 70 + 16 * (nb if pads else 1) - 6
        out.append('          <path class="d-line" d="M%d,%d H%d" stroke-opacity="0.3"/>' % (x + 10, ry, x + cw - 10))
        if supply:
            out.append('          <text class="d-x d-warn" x="%d" y="%d" text-anchor="middle">OPEN</text>' % (cx, ry + 20))
            out.append('          <text class="d-x" x="%d" y="%d" text-anchor="middle">at both ends</text>' % (cx, ry + 34))
            aria += 'Pin %d carries 3.3 V and is open at both ends. ' % n
        else:
            joined = ', joined' if role == 'ground' else ''
            out.append('          <text class="d-x" x="%d" y="%d" text-anchor="middle">straight: pin %d%s</text>' % (cx, ry + 20, straight, joined))
            out.append('          <text class="d-x" x="%d" y="%d" text-anchor="middle">mirrored: pin %d%s</text>' % (cx, ry + 34, mirrored, joined))
            if pads:
                where = '; '.join('%s %s' % (names[b], pads[b]) for b in boards)
            else:
                where = 'no package pin'
            aria += 'Pin %d, %s (%s), meets pin %d straight and pin %d mirrored%s. ' % (
                n, role, where, straight, mirrored, ', and the cable joins the two grounds' if role == 'ground' else '')
    body = '\n'.join(out)
    ty = ys[1] + ch + 36
    h = ty + 40
    title = 'the debug cable on a Pmod' if nb > 1 else 'the debug cable on the Kria KR260'
    sub_ = ('JA on the Arty Z7-20, PMOD1 on the Kria KR260; the pin each meets at the far Pmod, on a straight ribbon and on a mirrored one'
            if nb > 1 else 'PMOD1, with the pin each meets at the far Pmod, on a straight ribbon and on a mirrored one')
    return ('<svg viewBox="0 0 1060 %d" role="img" aria-label="%s">\n'
            '          <text class="d-t" x="10" y="18">%s</text>\n'
            '          <text class="d-s" x="10" y="36">%s</text>\n'
            '%s\n'
            '          <text class="d-s" x="50" y="%d">Pins 1 to 4 and 7 to 10 are the eight signals. Pins 5 and 11 are ground and the cable joins them;</text>\n'
            '          <text class="d-s" x="50" y="%d">pins 6 and 12 are each board&rsquo;s own 3.3 V, and the cable leaves them open at both ends.</text>\n'
            '        </svg>' % (h, aria.strip(), title, sub_, body, ty, ty + 16))

def kria_cable_section():
    """The Kria KR260's page: its own section for the cable, the connector as
    the debugging page draws it."""
    return section('cable', 'THE DEBUG CABLE', 'The debug <em>cable.</em>',
        'The board&rsquo;s end of the cable is PMOD1, the first of its four Pmod headers. Its pins, and what has run on them, are on <a href="debugging.html#pmod">the debugging page</a>.',
        '')

# ================================================================ debugging

def build_debugging():
    base = open(os.path.join(BASE, 'debugging.html')).read()
    comment = re.search(r'<!-- THESE FIGURES CARRY NO BLOCK COLOR.*?-->', base, re.S).group(0)
    # fde is the DE25-Nano's connector, which sits between the cable and the
    # protocol in the base page and on the page, so the two names either side
    # of it keep pointing at the drawings they always did.
    f1, f2, f3, fde, f4, f5 = svgs('debugging.html')
    # the first row is MIT's cable's drawing, which is on the CADR's page
    src_rows = open(os.path.join(HERE, 'dbg-src-rows.txt')).read()
    src_rows = re.sub(r'\n[ \t]*<tr><th scope="row">one CADR debugging another</th>.*?</tr>', '', src_rows, count=1, flags=re.S)
    assert 'one CADR debugging another' not in src_rows
    P = [comment, '\n']
    P.append(hero('muir-fpga &middot; debugging', 'Debugging a<br>Lisp <em>Machine.</em>',
                  'A CADR is debugged by another CADR. This page is how MIT did that, and how a board here does it.',
                  body='<div class="hero-description">\n'
                       '<p>The debugger is not a program on a host. It is a second Lisp Machine, running bus cycles on the first over a cable of twenty-one wires, as though it were that machine&rsquo;s own processor.</p>\n'
                       '<p>The program that drives the cable is CC, and it is Lisp software on the debugging machine.</p>\n'
                       '<p>Every board running the CADR is a debuggee the moment it is powered, which is what a CADR is with nothing set, and one of them can be told to be the debugger instead.</p>\n'
                       '</div>\n'))

    nfig = [0]
    def fig(svg, caption, title, more=''):
        nfig[0] += 1
        return figure(svg, caption, more=more, label='FIG. %02d &mdash; %s' % (nfig[0], upper(title)), name=title)

    # The heading carries the site's accent on its last words; the figure's
    # label is the same words without it.
    def plain(title):
        return re.sub(r'<[^>]+>', '', title.replace('<br>', ' '))

    def fig_section(n, sid, eyebrow, title, lead, svg, caption):
        return section(sid, '%02d / %s' % (n - 1, upper(eyebrow)), title, lead, fig(svg, caption, plain(title).rstrip('.')))

    # MIT's cable itself is drawn once, on the CADR's page; this section says
    # what CC does over it.
    P.append(section('mit', '01 / MIT&rsquo;S WAY', 'How MIT debugged<br>a <em>CADR.</em>',
        'The debugger&rsquo;s DBGOUT connector goes to the debuggee&rsquo;s DBGIN connector on its bus interface board, and a debugger works the cable by writing four registers of its own. <a href="../cadr/#cable">The CADR&rsquo;s page</a> draws the cable, its twenty-one wires and the four strobes they make.',
        '''<div class="prose">
<p>What CC does over the cable, every one of them a bus cycle on the other machine:</p>
<ul>
<li><code>CC-STOP-MACH</code>: one write of 0 to <code>0o766006</code>, and the machine halts where it stands.</li>
<li><code>SPY-READ</code>: any of the sixteen diagnostic registers, which is the machine&rsquo;s whole state as the console sees it.</li>
<li><code>CC-EXECUTE</code>: forces a microinstruction into the instruction register, which is how a scratchpad is read.</li>
<li><code>DBG-READ-XBUS</code>: writes Unibus map entry 17 and reads main memory through the window at <code>0o140000</code> that the map translates.</li>
<li><code>DBG-RESET</code>: the modifier register&rsquo;s bit 1, which resets the debuggee&rsquo;s Unibus and bus interface, and halts it.</li>
<li><code>PROG.BOOT</code>: bit 7 of a write to the mode register, one of the three ways a CADR can be told to boot.</li>
</ul>
</div>
''', label='How MIT debugged a CADR'))

    P.append(fig_section(3, 'fabric', 'On the boards', 'How the fabric<br><em>does it.</em>',
        'MIT&rsquo;s DBGIN logic is in the machine here, and so are the four DBGOUT registers CC writes, so a board can be either end of the cable.',
        f2,
        'Only the connector changes hands. A board&rsquo;s own DBGIN page is never switched off, so a debugger board stays debuggable through its window.'))

    P.append(fig_section(4, 'cable', 'Between two boards', 'The <em>cable.</em>',
        'A cable for this link joins the eight signals and the two grounds, and leaves the 3.3 V supply pins open at both ends.',
        f3,
        'The connector is Pmod JA on the Arty Z7-20. A board told to be the debugger listens on both groups of pins first, so a ribbon made the wrong way up is found rather than trusted.'))

    # THE TWO PMOD BOARDS: the Arty Z7-20 on JA, the
    # Kria KR260 on PMOD1.  One drawing carries the twelve pins, each board's
    # package pin and the pin each meets at the far Pmod; the section carries
    # what has run (the Arty, on a ribbon between its JA and another board's) and
    # the Kria's caveat (AMD's pin order, not checked on a wire, not run).
    P.append(section('pmod', '04 / THE TWO PMOD BOARDS', 'The cable on<br>the <em>Pmod boards.</em>',
        'The Arty Z7-20 carries the cable on Pmod JA and the Kria KR260 on PMOD1, the first of its four Pmod headers. On each the eight signal pins are 3.3 V, each with a pull-down, so an unplugged connector reads zero.',
        '''<div class="cols">
<div class="prose">
<p>The eight signals are on pins 1 to 4 and 7 to 10 of each connector, in the same order, so a straight ribbon between any two of them joins each signal to its counterpart. The Arty&rsquo;s package pins are from Digilent&rsquo;s file; the Kria&rsquo;s are AMD&rsquo;s.</p>
<p>A mirrored ribbon is one pressed on the other way up, which joins each row to the other, and the debugger finds it under <code>auto</code>.</p>
<p><b>The grounds are joined and the supplies are not.</b> Pins 5 and 11 are ground and the cable joins them. Pins 6 and 12 carry each board&rsquo;s own 3.3 V, and the cable leaves them open at both ends. Neither board&rsquo;s <code>.xdc</code> file names a supply pin, so nothing in the design can drive one.</p>
</div>
<div>
<p class="callout">The Arty has run this cable.</p>
<div class="prose"><p>A ribbon between its JA connector and another board&rsquo;s has carried the link, each board running Lisp throughout; the table below says what it carried.</p></div>
<p class="callout">The Kria&rsquo;s pin order is AMD&rsquo;s, and it has not been checked on a wire.</p>
<div class="prose"><p>The Kria&rsquo;s package pins and the order of its eight signals come from AMD&rsquo;s board files for the KR260. That the first eight pins in those files are header pins 1 to 4 and 7 to 10 is the order every Pmod pin file uses, and no schematic of the carrier is published to check it against. The Kria&rsquo;s cable has not been run on the boards: the connector is built into this board&rsquo;s CADR, the console reads a debuggee on it with nothing attached, and it has crossed nothing.</p></div>
</div>
</div>
''' + fig(pmod_cable_svg(), 'Each pin with what it carries, its package pin on each Pmod board, and the pin of the far Pmod it meets on a straight ribbon and on a mirrored one.',
          'The cable on the Pmod boards')))

    # THE DE25-NANO'S END, which is not a Pmod.  This section is where the
    # warning about the supply pins belongs: the front page carries it as a
    # line, and this is the page somebody reads with wire in their hand.  The
    # two things it has to say beyond the pin list are that the guards here
    # rest on a decision rather than on a schematic, and that no cable of this
    # shape exists, so nothing of this connector has been on hardware.
    P.append(section('de25', '05 / A GPIO HEADER, NOT A PMOD', 'The cable on<br>the <em>DE25-Nano.</em>',
        'That board has no Pmod, so its end of the cable is eight pins of a 2x20 GPIO header: JP1 pins 31 to 38, with the header&rsquo;s own ground on pin 30. The signals are on the odd pins and each guard is the even pin beside its signal.',
        fig(fde,
          'The drawing answers the three questions somebody holding wire has: which of the board&rsquo;s two headers, which end of it, and which pins must never be joined. Its notes say why the guards are there and that no such cable has been made.',
          'The cable on the DE25-Nano')))

    P.append(section('wire', '06 / FRAMES ON EIGHT PINS', 'The protocol<br>on the <em>wire.</em>',
        'Twenty-one wires do not fit on eight pins, so the levels cross as frames: four pins each way, and neither group is ever driven from both ends.',
        fig(f4, 'One signal to a pair of pins, the partner driven low as a guard: twenty-four beats, 162 ticks, a fraction of the 11.05 microseconds a debug cycle is allowed.', 'One frame, on the wire') +
        fig(f5, 'Twenty of MIT&rsquo;s signals cross one way and nineteen the other. The twenty-first bit each way is the carrier&rsquo;s own, and it is how two debuggees know neither is a debugger.', 'What crosses, each way')))


    rows = [
        ('The machine halted, and its registers read', 'CC through the register window, each register equal to the console&rsquo;s reading of the same halt', 'yes'),
        ('The scratchpads', 'CC&rsquo;s reads over the window, equal to the console&rsquo;s readout of the same words', 'yes'),
        ('Main memory, through the map', 'Words read through the mapped window, each equal to the console&rsquo;s reading of the same address; a write through the map moved MD and spent no microcycle', 'yes'),
        ('The ribbon between two boards', 'The role taken and given back on a real cable between two Pmod JA connectors, the far end answering', 'yes'),
        ('A mirrored ribbon, found by the fabric', 'The board told to connect reported the crossover it had found; forced the wrong way round, nothing answered', 'yes'),
        ('Two idle boards on that ribbon', 'Both read a debuggee with nothing driving the connector; the role bit tells the two apart', 'yes'),
        ('Neither machine noticing', 'Both boards ran Lisp throughout, at the rate they run at with no cable in them', 'yes'),
        ('CC over the ribbon', 'Halted, read and started again, both ways round, every word equal to the far board&rsquo;s own console and readout', 'yes'),
        ('Every microcycle accounted for', 'The far machine&rsquo;s cycle counter moved by one for each scratchpad read, and the debuggee&rsquo;s own window saw no request at all', 'yes'),
        ('The guards, and the frames refused', '0 refused in twenty-four readings; two frames on the other board are unaccounted for', 'yes'),
        ('A debug cycle over the guarded carrier', 'A status read typed at the debugger&rsquo;s Listener, both ways round; no register of the far machine crossed', 'yes'),
        ('CC over the guarded carrier', 'All sixteen of the far machine&rsquo;s diagnostic registers read over the guarded ribbon at one halt, each equal to the far board&rsquo;s own console, and the machine stepped and started over it; CC&rsquo;s own sequences typed at a Listener, and not the program run', 'yes'),
        ('A write over the ribbon', 'MD written over the ribbon by CC&rsquo;s own CC-WRITE-MD; the far board&rsquo;s own console read 0xa53c5ac3 where it read 0x0a0005c2 before and after the restore, and no microcycle was spent', 'yes'),
        ('The Kria KR260&rsquo;s connector', 'Nothing. No ribbon has joined PMOD1 to another board, so its eight pins have crossed nothing; the console reads a debuggee on it with nothing attached', 'not yet'),
        ('The DE25-Nano&rsquo;s connector', 'Nothing. No cable from a 2x20 header to a Pmod has been made, so those eight pins have crossed nothing; what reads them is lint and a check on the pin map', 'not yet'),
    ]
    trs = ''.join('<tr><th scope="row">%s</th><td>%s</td><td class="st%s">%s</td></tr>\n'
                  % (a, b, '' if c == 'yes' else ' no', c) for a, b, c in rows)
    P.append(section('shown', '07 / ON SILICON', 'What has run<br>on a <em>board.</em>',
        'All three pieces have run on silicon: the window, the ribbon, and CC across the ribbon, both ways round, a write into a register of the far machine among them. Over the guarded carrier, what has crossed is every cycle a CC session is built out of, typed at a Listener; the CC program itself has not run over it.',
        '''<div class="table-scroll" tabindex="0" role="region" aria-label="What has run on a board"><table>
<thead><tr><th scope="col">What</th><th scope="col">How it was shown</th><th scope="col">Shown</th></tr></thead>
<tbody>
%s</tbody>
</table></div>
<p class="small-print"><code>yes</code> means a board itself has shown it, which is not the claim a board drawing&rsquo;s green makes: green says a block is this project&rsquo;s work and done, which is built and checked rather than run on that board.</p>
''' % trs))

    P.append(section('sources', '08 / SOURCES', 'Where each drawing<br><em>came from.</em>',
        'Each figure above was read from the sources listed here. A number with a leading <code>0o</code> is octal, which is how MIT writes an address.',
        '''<div class="table-scroll" tabindex="0" role="region" aria-label="Where each drawing came from"><table>
<thead><tr><th scope="col">Figure</th><th scope="col">Read from</th></tr></thead>
%s</table></div>
''' % src_rows))
    page('debugging.html', 'muir-fpga &mdash; debugging',
         'How one CADR debugs another over MIT&rsquo;s debug cable, and how a board here does it: the debuggee&rsquo;s end in the fabric, a register window for a debugger on the board&rsquo;s own Arm cores, a ribbon between two boards on one Pmod connector, and the same eight signals on eight pins of a 2x20 header.',
         P)

# ================================================================ the CADR

def build_cadr():
    """What the CADR is, board by board, is the machine's own page, /cadr/;
    this page says so, and keeps every anchor it had, each a line that
    leads to the same drawing there."""
    P = [hero('muir-fpga &middot; CADR', 'CADR',
              'What the CADR is, board by board, is on its own page among the machines.',
              body='<p class="hero-description">muir-fpga puts it in the fabric of <a href="index.html#boards">FPGA boards</a>; the drawings of the machine itself, read from MIT&rsquo;s own files, are on the CADR&rsquo;s page.</p>\n',
              keys=keys(('../cadr/', 'CADR'), ('index.html', 'The boards')))]
    items = [('whole', 'The whole machine'), ('processor', 'The processor'), ('word', 'The microinstruction'),
             ('macro', 'The macroinstruction'), ('map', 'The map'), ('where', 'What is where'),
             ('disk', 'The disk'), ('display', 'The display'), ('io', 'The I/O board'),
             ('panel', 'The light panel'), ('cable', 'The debug cable'), ('sources', 'Where each drawing came from')]
    lis = ''.join('<li id="%s"><a href="../cadr/#%s">%s</a>.</li>\n' % (i, i, t) for i, t in items)
    P.append(section('drawings', '01 / WHERE ITS DRAWINGS ARE', 'On the machine&rsquo;s <em>page.</em>', '',
                     '<div class="prose"><ul>\n%s</ul></div>\n' % lis, label='Where the drawings are'))
    page('cadr.html', 'muir-fpga &mdash; the CADR',
         'What the MIT CADR Lisp Machine is, in drawings of the whole machine, its processor and its boards, is on the CADR&rsquo;s own page among the machines.',
         P)


# ================================================================ questions


FAQ = [
  ('The machine', [
    ('Why is there no disk multiplexor block?',
     'MIT built one, board type LG684, and its work is electrical: it fans the controller&rsquo;s one read and write path out to eight drives. Here a drive is a file on the card, so there is nothing for such a board to do, and the controller selects among eight units by <code>DA&lt;30:28&gt;</code> as MIT&rsquo;s does.',
     'MIT&rsquo;s <code>mit/cadrdc/dm.txt</code>, <code>dm.wls</code>, <code>dm.eco</code> and <code>disk.hand</code>; muir&rsquo;s <code>src/cable.rs</code> and <code>src/disk_controller.rs</code>; <code>docs/disk-controller.md</code>'),
    ('Why is muir-sim the reference, and what does "held tick for tick" mean?',
     'A machine with no reference is a machine nobody can check. Each file in <code>rtl/machine/</code> is compared against a muir type over a recorded trace, cycle for cycle, and <code>muir.commit</code> names the muir the traces were taken from.',
     '<code>README.md</code>; the header of <code>mutations/list.txt</code>'),
    ('Why is a tick ten nanoseconds?',
     'Because the design does not meet its timing with a 5&nbsp;ns clock. The CADR placed its clock edges with delay lines, and here each of MIT&rsquo;s instants goes to the first 10&nbsp;ns tick at or after it, so some edges fall up to 7&nbsp;ns later, and the processor and its clocks run within about 5% of the original speed. muir&rsquo;s fpga timing model rounds the same way.',
     '<code>docs/timing.md</code>; the header of <code>rtl/machine/cadr_tick_pkg.sv</code>; <code>README.md</code>'),
    ('Does the machine&rsquo;s own clock agree with the wall?',
     'Yes, while the grid and the tick are the same number: the microsecond clock counts 100 ticks, one real microsecond, and the vertical interrupt arrives at the rate of the sync program the board runs: 64.70 Hz from MIT&rsquo;s PROM program until the band loads its own, and 60.503 Hz from <code>CPT-SYNC2</code>, which every boot loads.',
     '<code>docs/io-board.md</code>, <code>docs/tv.md</code>, <code>docs/board.md</code>'),
    ('Is the color TV four bits a pixel or eight?',
     'Four, and nothing here implements eight: a pixel is a four-bit address into a map of sixteen colors, each of three eight-bit channels.',
     '<code>docs/tv.md</code>; muir&rsquo;s <code>src/tv.rs</code>; MIT&rsquo;s <code>sys/window/color.lisp</code>, <code>sys/ucadr/uc-hacks.lisp</code> and <code>cadrtv/lmtv.order</code>'),
    ('Why does the screen keep the previous boot&rsquo;s picture?',
     'Because the real machine did: no reset clears the frame buffer, and MIT wrote the clear in software, which runs when the band comes up.',
     '<code>docs/tv.md</code>; MIT&rsquo;s <code>sys/sys/ltop.lisp</code> in the System 100 release'),
  ]),
  ('The boards, and the way they are checked', [
    ('Why is the debug cable on one Pmod connector?',
     'A board is a debugger or a debuggee and never both at once, and neither group of four pins is ever driven from both ends, so one connector carries the whole link both ways.',
     '<code>docs/debug-cable.md</code>'),
    ('How does a board become the debugger?',
     'With <code>--debug-cable-connect</code> in <code>fpgarc</code> at boot, or <code>cadr-console debug-cable-connect</code> at any time. With nothing said, a board is a debuggee.',
     '<code>docs/debug-cable.md</code>'),
    ('Why are the checks themselves mutation-tested?',
     '<code>make check</code> says the checks pass. <code>make mutants</code> says the checks can still fail.',
     '<code>docs/mutations.md</code>'),
    ('Why is there no ILA or other Vivado debug core?',
     'The free BASIC tier refuses <code>create_debug_core</code>, so the probe is a <code>BSCANE2</code> and a shift register, which fills from reset and freezes with nobody at the board.',
     'the header of <code>rtl/plumbing/cadr_probe.sv</code>; <code>docs/toolchain.md</code>'),
    ('What license is this under, and what in it is not this project&rsquo;s work?',
     'The GNU Affero General Public License, version 3 or later, apart from four files compiled into U-Boot under the GPL, version 2 or later. The third-party material is on <a href="index.html#license">the boards page</a>.',
     '<code>docs/license.md</code>'),
  ]),
]

# Each group's eyebrow and heading, the heading with the site's accent.
FAQ_EYEBROW = tuple('%s QUESTIONS' % NUMBER[len(qs)].upper() for _, qs in FAQ)
FAQ_TITLE = ('The <em>machine.</em>', 'The boards, and the way<br>they are <em>checked.</em>')

def build_faq():
    base = open(os.path.join(BASE, 'faq.html')).read()
    comment = re.search(r'<!-- EVERY ANSWER HERE RESTS ON A FILE.*?-->', base, re.S).group(0)
    P = [comment, '\n']
    P.append(hero('muir-fpga &middot; questions', 'Questions',
                  'Questions this project is asked, each answered from the file that settles it.',
                  body='<p class="hero-description">Each answer here is a sentence or two. MIT&rsquo;s own files are cited at the path <a href="../simulator/">muir-sim</a> gives them, and the rest are files here.</p>\n'))
    # THE QUESTIONS ARE docs/faq.md's HEADINGS, word for word, so a question
    # keeps the document's wording even where the site's would differ.
    # site_terms() still renames a bare muir to muir-sim in the visible text
    # of the other questions.
    n = 1
    for group, qs in FAQ:
        cells = ''
        for q, a, src in qs:
            cells += '''<div class="qa">
<h3>%s</h3>
<p>%s</p>
<p class="src">Rests on %s.</p>
</div>
''' % (q.replace('"', '&ldquo;', 1).replace('"', '&rdquo;', 1), a, src)
        P.append(section(None, '%02d / %s' % (n, FAQ_EYEBROW[n - 1]), FAQ_TITLE[n - 1], '', cells, label=group))
        n += 1
    page('faq.html', 'muir-fpga &mdash; questions',
         re.search(r'<meta name="description" content="([^"]*)">', base).group(1), P)

# ================================================================ run

def main(out):
    """Write every page into `out`, and return their names."""
    global OUT
    OUT = out
    os.makedirs(OUT, exist_ok=True)
    del WRITTEN[:]
    build_index()
    build_board('arty-z7-20.html', 'Arty Z7-20', 'QUUX and the CADR mapped onto one AMD Zynq 7020, the XC7Z020.', "muir-fpga's board, waving",
                ('kria-kr260.html', 'Kria KR260'), DIGILENT_ARTY, quux=quux_svg('arty-z7-20'))
    build_kr260()
    build_de25()
    build_booting()
    build_debugging()
    build_cadr()
    build_faq()
    if os.environ.get('FIT_REPORT'):
        for where, text in fit.UNFITTED:
            print('unfitted', where, text, file=sys.stderr)
    return list(WRITTEN)

if __name__ == '__main__':
    main(sys.argv[1])
