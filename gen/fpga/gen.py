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
OUT = None     # set by main()
GH = 'https://github.com/metebalci/muir-fpga/blob/main/docs/'

# THE MAKERS' OWN PAGES FOR THE BOARDS.  Each was opened in a browser and read to
# be that board's product page before it was written here: Digilent's "Arty Z7:
# Zynq-7000 SoC Development Board", whose options are the Arty Z7-20 and the
# Arty Z7-10; Digilent's "Cora Z7: Zynq-7000 Single Core for ARM/FPGA SoC
# Development", which sells the Cora Z7-07S; and Terasic's "DE25-Nano
# Development and Education Board", whose specifications give the FPGA as
# A5EB013BB23BE4SCS.  The ampersands are written as HTML wants them.
DIGILENT_ARTY = 'https://digilent.com/shop/arty-z7-zynq-7000-soc-development-board/'
DIGILENT_CORA = 'https://digilent.com/shop/cora-z7-zynq-7000-single-core-for-arm-fpga-soc-development/'
TERASIC_DE25 = 'https://www.terasic.com.tw/cgi-bin/page/archive.pl?Language=English&amp;CategoryNo=115&amp;No=1384'

def svgs(page):
    t = open(os.path.join(BASE, page)).read()
    return re.findall(r'<svg\b.*?</svg>', t, re.S)

def slug(h):
    h = h.lower()
    h = ''.join(c for c in h if c.isalnum() or c in ' -_')
    return h.replace(' ', '-')

def sub(text, old, new, count=1):
    """Replace a figure, asserting it appears exactly as often as expected, so
    a drawing that has moved under the generator stops the run."""
    n = text.count(old)
    assert n == count, (old[:80], n, count)
    return text.replace(old, new)

# THE FIT FIGURES ON THE DRAWINGS, from each board's own place and route
# report.  Both boards were built from a clean tree at 9d1cf26, whose
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
def slack_block(ns):
    """The comment and the one label, to stand under a drawing's last bar.
    No leading or trailing newline: the caller joins it to the line above."""
    return ('          <!-- The worst setup slack of that build, and only the worst\n'
            '               value: the rest of what the fit reported about timing is\n'
            '               in the comment above the bars and is not drawn.  It sits\n'
            '               on the same row pitch the two bars keep and carries no\n'
            '               bar of its own, because a slack has no total to be a\n'
            '               fraction of. -->\n'
            '          <text class="d-s" x="-164" y="140">worst setup %s ns</text>' % ns)

ARTY_FIT = [
    ('The CADR mapped onto one XC7Z020.', 'The CADR mapped onto one Xilinx Zynq 7020, part XC7Z020-1CLG400C.'),
    ('Slices 5,441 of 13,300', 'LUTs 15,050 of 53,200'),
    ('<rect x="-164" y="74" width="55.6" height="13" fill="currentColor" fill-opacity="0.42"/>',
     '<rect x="-164" y="74" width="38.5" height="13" fill="currentColor" fill-opacity="0.42"/>'),
    ('<text class="d-n" x="-158" y="84">40.9%</text>', '<text class="d-n" x="-158" y="84">28.3%</text>'),
    ('5,441 of the 13,300 slices occupied, 40.9 per cent, which is a conservative figure since a fuller design packs tighter',
     '15,050 of the 53,200 lookup tables in use, 28.3 per cent'),
    ('and 205 KB of the 630 KB of block RAM, 32.5 per cent; and the timing of this build, which is met --- the fabric runs at 100 megahertz with a tick of 10 nanoseconds, worst slack plus 0.176 nanoseconds against that, and none of its 54,072 endpoints failing. ',
     'and 207 KB of the 630 KB of block RAM, 32.9 per cent. Under those two figures, the worst setup slack of this build, plus 0.222 nanoseconds. '),
    ('<text class="d-s" x="-164" y="104">BRAM 205 KB of 630 KB</text>',
     '<text class="d-s" x="-164" y="104">BRAM 207 KB of 630 KB</text>'),
    ('<rect x="-164" y="110" width="44.2" height="13" fill="currentColor" fill-opacity="0.42"/>',
     '<rect x="-164" y="110" width="44.7" height="13" fill="currentColor" fill-opacity="0.42"/>'),
    ('<text class="d-n" x="-158" y="120">32.5%</text>',
     '<text class="d-n" x="-158" y="120">32.9%</text>\n' + slack_block('+0.222')),
    ("""          <!-- Slack is a build's figure and not the design's, and it moves by a
               quarter of a nanosecond between builds of identical logic ---
               measured, at two commits whose RTL is identical. It is here at
               request, for now, with the count beside it because the
               worst path alone says nothing about how much is wrong, and with
               the clock above it because a slack in nanoseconds means nothing
               without the period it is slack against: +0.176 ns of a 10 ns
               tick is room over the deadline, and of a 5 ns tick it would
               not be. -->
          <text class="d-s" x="-164" y="144">100 MHz, 10 ns a tick</text>
          <text class="d-s" x="-164" y="160">worst slack +0.176 ns</text>
          <text class="d-s" x="-164" y="176">failing 0 of 54,072</text>
          <rect class="d-box" x="-164" y="182" width="136" height="13"/>
          <text class="d-n" x="-158" y="192">0%</text>
""", ""),
    ("""          <!-- What the machine costs on the part: the memory-on board with the
               disk and both display boards in it, place and routed with DDR=1,
               HDMI=1 and LMTV=1, which is the fabric the board runs.  Built at
               cc8594c from a clean tree, which is the commit these figures are
               of: the bitstream's own stamp reads cc8594c0.
               The baseline is b42bbc8, place and routed by the same flow with
               the same three switches: 5,957 slices at 44.8 per cent, 42.5
               block RAM tiles at 30.4 per cent, five DSPs, and a worst slack
               of +0.327 ns on 0 of 55,650 endpoints.  TWO changes lie between
               the two commits and not one --- the display output's rotation
               and color, and the Chaosnet card's count of the frames it
               refused, which landed beside it --- and together they cost 516
               slices FEWER, one DSP fewer and three block RAM tiles more.
               The display's own share was measured against that same baseline
               before the other change landed: 655 slices fewer and the DSP,
               because the line address became a register that adds a stride
               once a line where it had been a multiplication made on every
               pixel; and all three block RAM tiles, which are the two band
               buffers a turned picture reads its word columns into.
               Two rows,""",
     """          <!-- What the machine costs on the part: the memory-on board with the
               disk and both display boards in it, place and routed with DDR=1,
               HDMI=1 and LMTV=1, which is the fabric the board runs.  Built from the
               working tree on ab41da7 with the change that gives QUUX's
               control store an explicit block RAM enable, as muir-fpga's
               docs/fits.md records it; the Cora Z7-07S's
               drawing carries that board's figures from the same fits.  The
               46 block RAM tiles include the display output's two band
               buffers, which is the gap between this board's 46 and the Cora
               Z7-07S's 43, that board having no display output in it.  Timing
               is met on both edges: +0.222 ns of setup and +0.042 ns of hold.
               Two rows,"""),
    # THE ROW'S UNIT CHANGED FROM OCCUPIED SLICES TO LOOKUP TABLES, and the
    # rationale in the base page argued for the one it no longer carries, so
    # the whole of it is replaced rather than patched.  A slice is counted as
    # occupied the moment anything at all sits in it, so the count says how
    # spread out a design is as much as how large it is; a lookup table is a
    # direct measure of logic, and so is the DE25-Nano's ALM.  The slice figure
    # stays in the comment, because the part does run out of slices before it
    # runs out of lookup tables and a reader of this drawing should be able to
    # see that.
    ("""the same two on every board's drawing: occupied slices
               and block RAM. Occupied slices rather than lookup tables,
               because a slice counts as occupied the moment anything in it is
               used and that is the resource that runs out --- though it is
               elastic, since a fuller design packs tighter. 14,484 lookup
               tables and 11,069 flip-flops sit inside those 5,441 slices.""",
     """the same two on every board's drawing: the lookup tables
               in use and block RAM. Lookup tables rather than the occupied
               slices this row carried until now, because a slice counts as
               occupied the moment anything at all sits in it, so the count
               overstates how full a part is, while a lookup table is a direct
               measure of logic and so is the ALM the DE25-Nano's drawing
               reports. Those built as memory rather than as logic, which is
               where the machine's small memories go, are inside this figure
               and never reported beside it. Those lookup tables sit in 5,529
               of the part's 13,300 slices, 41.6 per cent, which is the figure
               this row used to show."""),
]
CORA_FIT = [
    ('The CADR mapped onto one XC7Z007S, the small Zynq on a Cora Z7-07S.',
     'The CADR mapped onto one Xilinx Zynq 7007S, part XC7Z007S-1CLG400C.'),
    ("MIT's own CC, running in the Lisp world of the CADR in the larger board's fabric,",
     "MIT's own CC, running in the Lisp world of the CADR in the Arty Z7-20's fabric,"),
    ('two lamps cannot carry what six carry on the larger board:', 'two lamps cannot carry what six carry on the Arty Z7-20:'),
    ("the part's own single Cortex-A9 core at 650 megahertz, this part having one where the Arty Z7-20 has two, drawn gray",
     "the part's own single Cortex-A9 core at 650 megahertz, drawn gray"),
    ('''because the drawing is the larger
               board's and what a reader wants''',
     '''because the drawing is the Arty
               Z7-20's and what a reader wants'''),
    ('This is the same design the larger board carries,', 'This is the same design the Arty Z7-20 carries,'),
    ("CC, in the Lisp world of the CADR in the larger board's fabric,", "CC, in the Lisp world of the CADR in the Arty Z7-20's fabric,"),
    ("board's own CC did the same to the larger board.  Every word", "board's own CC did the same to the Arty Z7-20.  Every word"),
    ('''The block is the larger board's, at its own place and
               its own size, and its six rows are the larger board's six.''',
     '''The block is the Arty Z7-20's, at its own place and
               its own size, and its six rows are the Arty Z7-20's six.'''),
    ('Slices 4,228 of 4,400', 'LUTs 14,024 of 14,400'),
    ('<rect x="-164" y="74" width="130.7" height="13" fill="currentColor" fill-opacity="0.42"/>',
     '<rect x="-164" y="74" width="132.4" height="13" fill="currentColor" fill-opacity="0.42"/>'),
    ('<text class="d-n" x="-158" y="84">96.1%</text>', '<text class="d-n" x="-158" y="84">97.4%</text>'),
    ('3,999 of the 4,400 slices occupied, 90.9 per cent; and 187 KB of the 225 KB of block RAM, 83.0 per cent. The machine spends the same 41.5 block RAM tiles here as it does on the larger part, so what changes between the two boards is the denominator.',
     '14,024 of the 14,400 lookup tables in use, 97.4 per cent; and 194 KB of the 225 KB of block RAM, 86.0 per cent. The machine spends 43 block RAM tiles here. Under those two figures, the worst setup slack of this build, plus 0.210 nanoseconds.'),
    ('<text class="d-s" x="-164" y="104">BRAM 191 KB of 225 KB</text>',
     '<text class="d-s" x="-164" y="104">BRAM 194 KB of 225 KB</text>'),
    ('<rect x="-164" y="110" width="115.6" height="13" fill="currentColor" fill-opacity="0.42"/>',
     '<rect x="-164" y="110" width="117" height="13" fill="currentColor" fill-opacity="0.42"/>'),
    ('<text class="d-n" x="-158" y="120">85.0%</text>',
     '<text class="d-n" x="-158" y="120">86.0%</text>\n' + slack_block('+0.210')),
    ('The timing of this build is met: the fabric runs at 100 megahertz with a tick of 10 nanoseconds, worst slack plus 0.494 nanoseconds against that, and none of its 47,909 endpoints failing. ', ''),
    ("""          <!-- Slack is a build's figure and not the design's, and it moves by a
               quarter of a nanosecond between builds of identical logic ---
               measured, at two commits whose RTL is identical. It is here at
               request, for now, with the count beside it because the
               worst path alone says nothing about how much is wrong, and with
               the clock above it because a slack in nanoseconds means nothing
               without the period it is slack against: +0.237 ns of a 10 ns
               tick is room over the deadline, and of a 5 ns tick it would
               not be. -->
          <text class="d-s" x="-164" y="144">100 MHz, 10 ns a tick</text>
          <text class="d-s" x="-164" y="160">worst slack +0.237 ns</text>
          <text class="d-s" x="-164" y="176">failing 0 of 51,134</text>
          <rect class="d-box" x="-164" y="182" width="136" height="13"/>
          <text class="d-n" x="-158" y="192">0%</text>
""", ""),
    ("""               placed on a part with a quarter of the logic: 4,228 occupied
               slices of 4,400, 13,172 slice lookup tables of 14,400, 10,112
               slice registers of 28,800 and 42.5 block RAM tiles of 50, which
               is the same 42.5 tiles the larger part spends.  What changes
               between the two boards is the denominator.
               THE COLOR TV FITS AND CLOSES HERE, WHICH IS WHAT DECIDED THAT
               THIS BOARD KEEPS IT.  The same tree with LMTV=0 is 4,171 slices
               at 94.8 per cent, 41.5 tiles at 83.0 per cent and +0.294 ns on
               0 of 49,650 endpoints, so the second display board costs this
               part 57 slices and one block RAM tile.  The switch is there for
               a part that cannot afford it; this one can.
               Built from the color TV change on top of 261547d before it was
               committed; that change landed at 653ca22 with its fabric unchanged,
               so 653ca22 is the commit these figures are of.""",
     """               placed on this part: 14,024 slice lookup tables of 14,400,
               4,325 occupied slices of 4,400 and 43 block RAM tiles of 50.
               Timing is met on both edges: +0.210 ns of setup and +0.041 ns
               of hold.
               THE COLOR TV FITS AND CLOSES HERE, WHICH IS WHAT DECIDED THAT
               THIS BOARD KEEPS IT.  When that was decided, at d55b436, the same
               tree with LMTV=0 was 4,171 slices at 94.8 per cent, 41.5 tiles at
               83.0 per cent and +0.294 ns on 0 of 49,650 endpoints, so the
               second display board cost this part 57 slices and one block RAM
               tile.  Those are figures in the unit this drawing used then and
               they are left in it, because they are a comparison made at that
               commit and not a reading of this build.  The switch is there for
               a part that cannot afford it; this one can.
               These are the fit of the working tree on ab41da7 with the
               change that gives QUUX's control store an explicit block RAM
               enable, as muir-fpga's docs/fits.md records it; the Arty
               Z7-20's drawing carries that board's figures from the same
               fits."""),
    # THE ROW'S UNIT CHANGED, as it did on the Arty Z7-20's drawing, and the
    # rationale in the base page argued for the unit it no longer carries.  On
    # this part the two readings are furthest apart and the slice figure is
    # still the one that says how little room is left, so it stays in the
    # comment under the figure that replaced it.
    ("""the same two on every board's drawing: occupied slices
               and block RAM.  Occupied slices rather than lookup tables,
               because a slice counts as occupied the moment anything in it is
               used and that is the resource that runs out --- though it is
               elastic, since a fuller design packs tighter, which is what the
               gap between 96.1 per cent of the slices and 91.5 per cent of the
               lookup tables inside them is.""",
     """the same two on every board's drawing: the lookup
               tables in use and block RAM.  Lookup tables rather than the
               occupied slices this row carried until now, because a slice
               counts as occupied the moment anything at all sits in it, so the
               count overstates how full a part is, while a lookup table is a
               direct measure of logic and so is the ALM the DE25-Nano's
               drawing reports.  Those built as memory rather than as logic,
               which is where the machine's small memories go, are inside this
               figure and never reported beside it.  Those lookup tables sit in
               4,325 of the part's 4,400 slices, 98.3 per cent, which is the
               figure this row used to show and is still the one that says how
               little room is left on this part."""),
]
# MIT'S GRID MOVED FROM 5 ns TO 10 ns at 9d1cf26, and the drawings' clock
# label and aria-labels were moved with it on the pages themselves.  These
# follow them, so the generator regenerates what is committed.
GRID_10 = [
    ('<text class="d-s" x="96" y="176" text-anchor="middle">29 ticks = 290 ns</text>',
     '<text class="d-s" x="96" y="176" text-anchor="middle">15 ticks = 150 ns</text>'),
    ('runs at 100 MHz, 29 ticks to the microcycle, 290 nanoseconds of real time',
     'runs at 100 MHz, 15 ticks to the microcycle, 150 nanoseconds of real time'),
    ('for the 145 the drawings name', 'for the 145 the schematics name'),
]
# THE FABRIC'S LABEL on both Zynq drawings names the programmable logic in
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
CORA_FIT += GRID_10 + FABRIC_LABEL

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
     'There is one video mode and the bitstream fixes it: 1280 by 1024 at 60 hertz, on a pixel clock of 108 '
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
# The table has two words, yes and no, and one qualification on a yes.  The
# site already tried a wider vocabulary here --- a thing a board has, or has
# built but not shown, or is planned to have, or cannot have --- and it was cut
# to two, and that cut stands: the qualification is not a third grade but a
# footnote in the cell, and there is one of them.  IT IS THERE BECAUSE TWO
# UNLIKE FACTS WERE BOTH READING AS NO.  The Cora Z7-07S has no HDMI connector
# on it at all, and the DE25-Nano's debug cable is in every bitstream that
# board builds with no ribbon yet made for its header: one is an absence of
# hardware and the other an absence of testing, and a reader could not tell
# them apart.  What a cell still cannot carry goes in this note, in sentences,
# rather than into a fourth word or a mark nobody follows.
BOARDS_NOTE = ('The Arty Z7-20 and the DE25-Nano run QUUX and the CADR, and the Cora Z7-07S the CADR alone. '
               'A cell says yes where that board itself has run the thing, '
               'yes with a qualification where the thing is built into that board and nothing of it has run there yet, '
               'and no where the board does not have the thing at all. '
               'The two resource figures in each row are that board&rsquo;s own place and route report for the CADR&rsquo;s fabric, '
               'with the memory, the disk and both display boards in it, in that part&rsquo;s own terms: '
               'lookup tables and block RAM on the Zynq boards, ALMs and M20K blocks on the DE25-Nano, '
               'and memory built out of logic is counted inside the logic figure rather than beside it. '
               'The two logic columns are different units, so their counts do not compare and the percentage is the figure that does: '
               'by Altera&rsquo;s own guide for converting a Zynq-7000 design to an Agilex 5 one, an ALM is about 1.3 lookup tables. '
               'The fabric carries one video mode, 1280 by 1024 at 60 hertz, and these figures are of it; '
               'a second mode was tried once and is not built now, and '
               '<a href="https://github.com/metebalci/muir-fpga/blob/main/docs/display-output.md#a-retired-second-mode">its record</a> '
               'is in the display document. '
               'What a board has built and checked but never run is on that board&rsquo;s own page.')

INDEX_FIT = [
    ("""    <!-- One row a board. The figures are each board's own place and route
         report, both built from the color TV change, which landed at
         653ca22 with its fabric unchanged. They are the figures that board's own drawing carries""",
     """    <!-- One row a board. The figures are each board's own place and route
         report for the fabric that board runs, with the memory, the disk and
         both display boards in it: the CADR fits of the working tree on
         ab41da7 with the change that gives QUUX's control store an explicit
         block RAM enable, as muir-fpga's docs/fits.md records them. They are the figures that board's own drawing carries"""),
    ("""         under its fabric label. A cell says yes only where that board itself
         has shown the thing, which is the same claim the drawings' colors
         make. -->""",
     """         under its fabric label. A CELL HAS THREE READINGS AND NOT TWO: yes
         where that board itself has run the thing, yes with a qualification
         where the thing is built into that board and nothing of it has run
         there yet, and no where the board does not have the thing at all.
         The middle one was added because two unlike facts were both reading
         as no. The Cora Z7-07S has no HDMI connector on it at all, and the
         DE25-Nano's debug cable is in every bitstream that board builds with
         no ribbon yet made for its header. It is a footnote in the cell and
         not a third grade: the five-step status vocabulary this site retired
         is exactly what it must not grow back into, so there is one
         qualification here and it is spelled out in the note above.
         That yes was once said to be the same claim the drawings' colors
         make, and it no longer is: since the key was cut to three colors,
         green says a block is this project's work and done, which means built
         and checked rather than run on that board. So the DE25-Nano's drawing
         colors its debug cable adapter green while this table's cell for the
         same thing says yes with a qualification, and both are right about
         their own question. Each
         resource figure is named in its own part's terms, because one
         vendor's word for another's part would be wrong: lookup tables and
         block RAM on the Zynq boards, ALMs and M20K blocks on the DE25-Nano.
         Lookup tables rather than the occupied slices this table carried
         before, because a slice counts as occupied the moment anything at all
         sits in it, so the count overstates how full a part is; a lookup table
         and an ALM are both direct measures of logic. The two are still
         different units and the counts do not compare: Altera's own
         conversion guide puts one ALM at about 1.3 lookup tables, so the
         percentage is the figure to read across the rows. That is section 2.2,
         "AMD vs Altera FPGA Resource", of "Design Conversion Guidelines: AMD
         Zynq 7000 SoC and Ultrascale+ MPSoC to Agilex 5 FPGAs and SoCs",
         Altera document 826363, revision 2026-01-27:
         https://docs.altera.com/r/docs/826363/current/design-conversion-guidelines-amd-zynq-7000-soc-and-ultrascale-mpsoc-to-agilextm-5-fpgas-and-socs
         Memory built out of logic is counted inside the logic figure and never
         reported beside it, which is why neither column names it. Under each
         board's name are its FPGA's product name, its part number and a link
         to its maker's page for it, each on a line of its own so that the
         name column stays narrow on a phone. The debug cable is a column
         because it is a thing one of these boards has run and another has
         only built, and a table without it would read as though all three
         were level. -->"""),
    ("""            <th scope="col">Slices</th>
            <th scope="col">Block RAM</th>""",
     """            <th scope="col">Fabric logic</th>
            <th scope="col">Block memory</th>"""),
    ("""            <th scope="col">USB input</th>
          </tr>""",
     """            <th scope="col">USB input</th>
            <th scope="col">Debug cable</th>
          </tr>"""),
    ('<td class="num">5,441 of 13,300<span class="pc">40.9%</span></td>', '<td class="num">15,050 of 53,200<span class="pc">LUTs &middot; 28.3%</span></td>'),
    ('<td class="num">45.5 of 140<span class="pc">32.5%</span></td>', '<td class="num">46 of 140<span class="pc">block RAM &middot; 32.9%</span></td>'),
    ('<a href="arty-z7-20.html">Arty Z7-20</a><span class="pc">XC7Z020</span></th>',
     '<a href="arty-z7-20.html">Arty Z7-20</a><span class="pc">Xilinx Zynq 7020</span><span class="pc">XC7Z020</span><span class="pc">made by <a href="%s">Digilent</a></span></th>' % DIGILENT_ARTY),
    ('<a href="cora-z7-07s.html">Cora Z7-07S</a><span class="pc">XC7Z007S</span></th>',
     '<a href="cora-z7-07s.html">Cora Z7-07S</a><span class="pc">Xilinx Zynq 7007S</span><span class="pc">XC7Z007S</span><span class="pc">made by <a href="%s">Digilent</a></span></th>' % DIGILENT_CORA),
    # The Arty Z7-20's debug cable cell, placed by the row that follows it,
    # which is the only text that says where this row ends.
    ('''            <td class="st">yes</td>
          </tr>
          <tr>
            <th scope="row" class="board"><a href="cora-z7-07s.html">Cora Z7-07S</a>''',
     '''            <td class="st">yes</td>
            <td class="st" title="Run over a real ribbon between this board and the Cora Z7-07S.">yes</td>
          </tr>
          <tr>
            <th scope="row" class="board"><a href="cora-z7-07s.html">Cora Z7-07S</a>'''),
    # The Cora Z7-07S's debug cable cell and the whole of the DE25-Nano's row.
    # ITS TWO FIGURES ARE THE ONES ITS OWN DRAWING CARRIES, from the fit of the
    # memory board with the display in it, the fit of the working tree on
    # ab41da7 that docs/fits.md records: 16,451 ALMs of 46,800 and 135 M20K blocks of 358, which is the same kind of build as the two Zynq
    # rows and the build its card carries.  The cores are the board's manual,
    # section 2.2 on page 8, through `boards/de25-nano/README.md`, and so are
    # the Ethernet, the card slot and the USB port, which are the processor's.
    # THE DEBUG CABLE IS THE ONE QUALIFIED YES, AND THE ONLY CELL IN THE TABLE
    # THAT CARRIES A QUALIFICATION.  The connector is in every build of this
    # board and every module under it is checked, but no cable from a 2x20
    # header to a Pmod has been made, so nothing of it has run on this board.
    # It read `no` for one day, beside the Cora Z7-07S's `no` for HDMI, and the
    # two are not the same fact: that board has no connector at all and this
    # one has the thing built and untested.  The qualification goes on a line
    # of its own under the word, in the same `pc` span the resource cells use
    # for their unit, so the column does not widen for it.
    ('''            <td class="st no" title="The board has no USB host port, so the image leaves the program out.">no</td>
          </tr>
        </tbody>''',
     '''            <td class="st no" title="The board has no USB host port, so the image leaves the program out.">no</td>
            <td class="st" title="Run over a real ribbon between this board and the Arty Z7-20.">yes</td>
          </tr>
          <tr>
            <th scope="row" class="board"><a href="de25-nano.html">DE25-Nano</a><span class="pc">Altera Agilex 5 E-series</span><span class="pc">A5EB013B</span><span class="pc">made by <a href="%s">Terasic</a></span></th>
            <td class="cpu">2 x Arm Cortex-A76 and 2 x Cortex-A55, Linux</td>
            <td class="num">16,451 of 46,800<span class="pc">ALMs &middot; 35.2%%</span></td>
            <td class="num">135 of 358<span class="pc">M20K &middot; 37.7%%</span></td>
            <td class="st">yes</td>
            <td class="st" title="The board's own card slot. This part has no card configuration scheme, so the flash carries the first stage and the card carries everything else.">yes</td>
            <td class="st">yes</td>
            <td class="st">yes</td>
            <td class="st" title="The connector is in every build of this board, and no cable from its GPIO header to a Pmod has been made, so nothing of it has run here.">yes<span class="pc">(not tested)</span></td>
          </tr>
        </tbody>''' % TERASIC_DE25),
    ('<td class="num">4,228 of 4,400<span class="pc">96.1%</span></td>', '<td class="num">14,024 of 14,400<span class="pc">LUTs &middot; 97.4%</span></td>'),
    ('<td class="num">42.5 of 50<span class="pc">85.0%</span></td>', '<td class="num">43 of 50<span class="pc">block RAM &middot; 86.0%</span></td>'),
]


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

def page(fname, title, desc, parts, css=()):
    main = site_terms(''.join(parts))
    desc = site_terms(desc)
    html = chrome.page('fpga/' + fname, title, desc, main, section='fpga',
                       css=('drawings.css',) + tuple(css))
    open(os.path.join(OUT, fname), 'w', encoding='utf-8').write(html)
    WRITTEN.append(fname)

def hero(eyebrow, title, lede, body='', keys='', side=''):
    """The top of a page: its eyebrow, its title, its lede and anything
    under it, and the keys to the pages it leads to."""
    return ('<section class="page-hero wrap%s">\n<div>\n'
            '<p class="eyebrow"><span class="dot"></span>%s</p>\n<h1>%s</h1>\n'
            '<p class="intro">%s</p>\n%s%s</div>\n%s</section>\n'
            % ('' if side else ' solo', eyebrow, title, lede, body, keys, side))

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

def more_line(text):
    return '<p class="more">%s</p>\n' % text

def docs_link(text, path, anchor=''):
    return '<a href="%s%s%s">%s</a>' % (GH, path, '#' + anchor if anchor else '', text)


# ================================================================ front page

def build_index():
    base = open(os.path.join(BASE, 'index.html')).read()
    table = re.search(r'    <!-- One row a board\..*?</table>\n    </div>\n', base, re.S).group(0)
    for o, n in INDEX_FIT:
        table = sub(table, o, n)
    # The table's own classes are kept; the site's style.css styles them.
    table = table.replace('<div class="tablescroll" tabindex="0"', '<div class="table-scroll" tabindex="0"')
    P = []
    P.append(hero('muir-fpga &middot; QUUX and the CADR in FPGA fabric', 'QUUX and the CADR,<br>in <em>FPGA fabric.</em>',
                  'What runs on each of three small boards.',
                  keys=keys(('#boards', 'The boards'), ('../cadr/', 'The CADR'), ('../quux/', 'QUUX'),
                            ('https://github.com/metebalci/muir-fpga', 'GitHub &#8599;')),
                  side='''<div class="side">
<p>Every part of it is held to <a href="https://github.com/metebalci/muir-sim">muir-sim</a>, a simulator of the same machine:</p>
<pre>HELD TO   muir-sim, <b>tick for tick</b>
          and microcycle for microcycle
BOOTS     MIT&rsquo;s own system software,
          off a disk pack
PAINTS    the window system, on a screen
RUNS      its processor and clocks within
          about 5% of the CADR&rsquo;s speed</pre>
</div>
'''))

    # The two speech bubbles this section had are plain sentences now, in
    # the same words.
    P.append(section('what', '01 / WHAT IT IS', 'A CADR<br>in the <em>fabric.</em>', '', '''<div class="cols">
<div class="prose">
<p>muir-fpga puts QUUX and the CADR in the fabric of an FPGA. The CADR is the Lisp Machine MIT designed around 1978, and muir-fpga&rsquo;s CADR is <a href="https://github.com/metebalci/muir-sim">muir-sim</a>&rsquo;s RTL model of it, synthesized into the fabric of an FPGA &mdash; the two processor boards, the bus interface, the disk controller, the display and the I/O board.</p>
</div>
<div class="prose">
<p>Its clock edges are close to the CADR&rsquo;s but not identical. The CADR placed them with delay lines, and the FPGA can place them only on the ticks of one 10&nbsp;ns clock, so some fall up to 7&nbsp;ns later. <a href="https://github.com/metebalci/muir-fpga/blob/main/docs/timing.md">The timing, instant by instant</a>.</p>
<p>The same fabric is built as QUUX too, the CADR evolved: a card&rsquo;s <code>fpgarc</code> says which machine its bitstream is, with <code>--machine cadr</code> or <code>--machine quux</code> (<a href="https://github.com/metebalci/muir-fpga/blob/main/docs/fpgarc.md">docs/fpgarc.md</a>). QUUX runs on the Arty Z7-20 and the DE25-Nano, and the Cora Z7-07S builds the CADR alone. The CADR boots MIT&rsquo;s own system software; QUUX&rsquo;s system is muir-sys&rsquo;s updated one. A CADR band gets its files and the time from <a href="../ozd/">ozd</a>, the CADR&rsquo;s file and time host; a QUUX card does not start it.</p>
<p class="callout">QUUX is still being developed: its hardware revisions, microcode and system change, and a later QUUX need not run today&rsquo;s bands or microcode.</p>
<div class="actions"><a class="text-link" href="arty-z7-20.html">Arty Z7-20</a><a class="text-link" href="cora-z7-07s.html">Cora Z7-07S</a><a class="text-link" href="de25-nano.html">DE25-Nano</a></div>
</div>
</div>
'''))

    P.append(section('boards', '02 / THE BOARDS', 'Three boards,<br>and what <em>each runs.</em>', BOARDS_NOTE, table))

    P.append(section('machine', '03 / THE MACHINES THEMSELVES', 'The real<br><em>machines.</em>', '', '''<div class="prose">
<p>What the two machines are, their processors, buses and devices, is on their own pages: QUUX, the CADR evolved, and the CADR, MIT&rsquo;s machine as it was built, board by board. It is worth knowing what a machine is before looking at a drawing of it inside a chip.</p>
<div class="actions"><a class="text-link" href="../cadr/">The CADR</a><a class="button" href="../quux/">QUUX</a></div>
</div>
'''))

    # THE LICENSE TABLE FOLLOWS docs/license.md, which is its long form and
    # its source: the work in the repository no longer includes pages, and
    # the fonts are the site's, not muir-fpga's, so their row is gone.
    rows = [
        ('The work in this repository: the fabric, the checks and their reference traces, the programs beside the machine and the documents',
         'This project&rsquo;s. <b>GNU Affero General Public License, version 3 or later</b>',
         '<a href="https://github.com/metebalci/muir-fpga/blob/main/LICENSE"><code>LICENSE</code></a>, and the SPDX identifier <code>AGPL-3.0-or-later</code> in almost every file&rsquo;s header'),
        ('Eight files, four for each Zynq board: <code>ps7_init_gpl.c</code>, U-Boot&rsquo;s default environment, the board&rsquo;s device tree and the <code>-u-boot.dtsi</code> beside it',
         'This project&rsquo;s, under the <b>GNU General Public License, version 2 or later</b>, because each is compiled into U-Boot',
         'each file&rsquo;s own header'),
        ('Digilent&rsquo;s pin files',
         'Digilent&rsquo;s, under the <b>MIT License</b>',
         '<code>Digilent-License.txt</code> beside the Cora Z7-07S&rsquo;s master file; the Arty Z7-20&rsquo;s constraint file cites the commit and digest of its pins'),
        ('<a href="https://github.com/metebalci/muir-sim">muir-sim</a>',
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
                     'Where nothing records the terms, the table says so instead of guessing. The long form is %s.' % docs_link('docs/license.md', 'license.md'),
                     '''<div class="table-scroll" tabindex="0" role="region" aria-label="License and third-party material"><table class="terms">
<thead><tr><th scope="col">What</th><th scope="col">Whose, and the terms</th><th scope="col">Where the terms are recorded</th></tr></thead>
<tbody>
%s</tbody>
</table></div>
''' % trs, label='License and third-party material'))

    P.append(section('colophon', '05 / ABOUT', 'Almost nothing here<br>is a <em>first-hand</em> invention.', '', '''<div class="prose">
<p>The CADR, the schematics, the wire lists and the microcode are MIT&rsquo;s, recovered by other people&rsquo;s work over decades, and the machine in the fabric is held tick for tick to <a href="https://github.com/metebalci/muir-sim">muir-sim</a>; <a href="https://github.com/metebalci/muir-fpga/blob/main/docs/cadr.md#sources">the documents list every source</a> the drawings were read from and what each one is.</p>
<p>muir-fpga is written with <a href="https://claude.com/claude-code">Claude Code</a>, using Anthropic&rsquo;s Claude Opus, Claude Fable and Claude Sonnet. The machine is written in SystemVerilog, its testbenches in C++ for Verilator, the programs beside it on the board in C, and the generators of its reference traces in Rust.</p>
<p>muir-fpga is muir-sim&rsquo;s RTL model of the CADR and of QUUX, synthesized into the fabric of an FPGA and held to muir-sim tick for tick.</p>
<p><b>&copy; 2026 Mete Balci.</b> muir-fpga is <a href="https://www.gnu.org/licenses/agpl-3.0.html">AGPL-3.0-or-later</a>. MIT&rsquo;s own files are not in this repository: muir-sim carries them, unmodified.</p>
<div class="actions"><a class="text-link" href="https://github.com/metebalci/muir-fpga/tree/main/docs">Read the documents &#8599;</a><a class="text-link" href="https://github.com/metebalci/muir-fpga/blob/main/docs/cadr.md#sources">The sources &#8599;</a><a class="text-link" href="https://github.com/metebalci/muir-fpga">Repository &#8599;</a></div>
</div>
''', label='About'))
    page('index.html', 'muir-fpga &mdash; the MIT CADR and QUUX in fabric',
         'The MIT CADR Lisp Machine and QUUX, the CADR evolved, in the fabric of small FPGA boards, held tick for tick to the muir-sim simulator: what runs on the Arty Z7-20, the Cora Z7-07S and the DE25-Nano.',
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

# Each word's advance in Zen Maru Gothic at 11 units, the face and size the
# drawing's `d-s` labels are set in.  The first of these were measured in
# Chromium with the site's own woff2 loaded, at 1,100 pixels and divided by a
# hundred, which is the face's own advance and not one rounded to a screen's
# pixels; a word measured at 11 pixels comes back rounded to whole pixels and
# would space the key by the screen rather than by the face.  The three words
# the key carries now are read out of the face itself, from
# fontsrc/zenmarugothic/ZenMaruGothic-Medium.ttf, which is what
# zen-maru-gothic-500.woff2 is built from and what a browser picks for `d-s`,
# since the file offers 500 and 700 and the rule asks 400: each glyph's
# advance from `hmtx`, the pair adjustments of the GPOS `kern` feature added,
# every one of them taken to 1.1 units and rounded half down, summed and
# divided by a hundred.  That rule reproduces all seven of the browser's own
# measurements to the hundredth --- including `not available on this board`,
# which is still in use --- which is why it is trusted for words no browser
# here has measured.
KEY_WIDTH = {
    'this project': 55.3,
    'another project': 74.99,
    'board component': 84.73,
    'not available on this board': 128.75,
}
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
KEY_ABSENT = ('d-absent-key', 'not available on this board')

def num(v):
    return ('%.2f' % v).rstrip('0').rstrip('.')

def frame(svg, fname, part, product):
    items = KEY_ITEMS + ([KEY_ABSENT] if fname == 'cora-z7-07s.html' else [])
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
        if cls == 'd-absent-key':
            key.append('''          <!-- The one mark on the drawing that is not about whose work a
               block is: a block this board does not have, kept in its place
               and crossed off.  The
               swatch is the drawing's own ink with the cross on it, because
               what the legend has to show here is the mark and not a color. -->
''')
        key.append('          <rect class="d-box%s d-key" x="%s" y="%d" width="13" height="13"/>\n'
                   % (' ' + cls if cls else '', num(x), KEY_SWATCH_Y))
        if cls == 'd-absent-key':
            key.append('          <path class="d-absent-x" d="M%s,%d L%s,%d M%s,%d L%s,%d"/>\n'
                       % (num(x), KEY_SWATCH_Y, num(x + 13), KEY_SWATCH_Y + 13,
                          num(x + 13), KEY_SWATCH_Y, num(x), KEY_SWATCH_Y + 13))
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
    for o, n in {'arty-z7-20.html': ARTY_FIT, 'cora-z7-07s.html': CORA_FIT}[fname]:
        svg = sub(svg, o, n)
    return frame(svg, fname, *{'arty-z7-20.html': ('XC7Z020-1CLG400C', 'Xilinx Zynq 7020'),
                               'cora-z7-07s.html': ('XC7Z007S-1CLG400C', 'Xilinx Zynq 7007S')}[fname])

# Every board page lists the other boards among its keys, the upcoming one last.
BOARD_KEYS = {
    'arty-z7-20.html': ('cora-z7-07s.html', 'Cora Z7-07S'),
    'cora-z7-07s.html': ('arty-z7-20.html', 'Arty Z7-20'),
}
DE25_KEY = ('de25-nano.html', 'DE25-Nano')

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
    'cora-z7-07s.html': 'muir-fpga &middot; Digilent &middot; Zynq 7007S',
    'de25-nano.html': 'muir-fpga &middot; Terasic &middot; Agilex 5 E-series',
}

def build_board(fname, name, lede, corner_label, other, maker):
    svg = board_svg(fname)
    title = re.search(r'<title>([^<]*)</title>', open(os.path.join(BASE, fname)).read()).group(1)
    board_page(fname, name, title, DESC[fname], lede, corner_label,
               (('booting.html', 'How it boots'), ('debugging.html', 'The debug cable'), other, DE25_KEY),
               maker, svg)

def board_page(fname, name, title, desc, lede, corner_label, key_list, maker, svg):
    # The board's name, the one line naming its FPGA, the keys to the other
    # pages with the maker's own page last, and the drawing, which is the
    # whole point of the page.  The corner character is gone; corner_label is
    # kept in the signature so that the calls below read as they did.
    P = [hero(BOARD_EYEBROW[fname], name, lede,
              keys=keys(*(tuple(key_list) + ((maker, 'The maker&rsquo;s page &#8599;'),)), first='key lm')),
         '<section class="section wrap tight" aria-label="%s, the drawing">\n' % name,
         figure(svg, '', cls='fig dense wide', label='FIG. 01 &mdash; %s' % name.upper(), name=name).replace('<figcaption></figcaption>\n', ''),
         '</section>\n']
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
            'It runs on a host of its own today, and no line reaches its block, because running it on this board&rsquo;s own processing system, so that a card by itself is a whole site, would be a path on the board and there is none yet. '
            'Under the fabric&rsquo;s label, two figures for the board with its memory, the disk and the display in it: 16,451 of the part&rsquo;s 46,800 adaptive logic modules in use, 35.2 per cent; and 135 of its 358 M20K blocks, 37.7 per cent. '
            'Under those two, the worst setup slack of this build, plus 1.663 nanoseconds. '
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

def de25_status():
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
    named = [(DE25_RENAME.get(name, name), s) for name, _, s in DE25_STATUS]
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
# Arty Z7-20's are.  They stand at zero until this board has a build.
DE25_FIT_NOTE = '''          <!-- From the Quartus fit of the CADR with the faces and the
               display output, the fit of the working tree on ab41da7 with
               the change that gives QUUX's control store an explicit block RAM
               enable, as muir-fpga's docs/fits.md records it.  Timing is met, the worst being +1.663 ns of setup, on an
               HDMI output pin, and 0.000 ns of hold.
               16,451 ALMs and 135 M20K blocks.
               A5E 013B: 46,800 ALMs, and 358 M20K blocks of 20 Kbit each,
               895 KB, the same convention as the Zynq boards' block RAM row.
               Source: Altera Agilex 5 E-Series Product Table, 2026.08.07, p. 3:
               https://docs.altera.com/api/khub/documents/rcQSreUhbuYGXCo7Np10cw/content
               The small memories are counted inside the ALMs, as the
               lookup-table memory on the Zynq boards is counted inside the
               slices. -->
'''
DE25_FIT = [
    ('ALM 16,451 of 46,800', 16451 / 46800),
    ('M20K 338 KB of 895 KB', 135 / 358),
]

def fit_bars(rows, y=68):
    out = ''
    for label, used in rows:
        # The percentage keeps one decimal always, as the Arty Z7-20's and the
        # Cora Z7-07S's own hand-written figures do (85.0%); num() would strip
        # a trailing zero, which reads as a different number of significant
        # figures than the same board's other row.
        out += ('          <text class="d-s" x="-164" y="%d">%s</text>\n'
                '          <rect class="d-box" x="-164" y="%d" width="136" height="13"/>\n'
                '          <rect x="-164" y="%d" width="%s" height="13" fill="currentColor" fill-opacity="0.42"/>\n'
                '          <text class="d-n" x="-158" y="%d">%.1f%%</text>\n'
                % (y, label, y + 6, y + 6, num(round(136 * used, 1)), y + 16, round(100 * used, 1)))
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
    i = svg.index('          <!-- What the machine costs on the part:')
    end = '          <text class="d-s" x="-164" y="140">worst setup +0.222 ns</text>\n'
    assert svg.count(end) == 1
    j = svg.index(end) + len(end)
    assert svg[i:j].count('LUTs 15,050 of 53,200') == 1 and svg[i:j].count('BRAM 207 KB of 630 KB') == 1
    assert svg[i:j].count('<text class="d-n" x="-158" y="120">32.9%</text>') == 1
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
    svg = sub(svg, '<text class="d-s" x="-164" y="24">Xilinx Zynq 7020 &middot; XC7Z020-1CLG400C</text>',
              '<text class="d-s" x="-164" y="24">%s &middot; %s</text>' % (DE25_PART[1], DE25_PART[0]))
    # (3) the memory
    svg = sub(svg, '''          <text class="d-t" x="87" y="738" text-anchor="middle">512 MB DDR3</text>
          <text class="d-s" x="87" y="762" text-anchor="middle">64 MB reserved for main memory,</text>
          <text class="d-s" x="87" y="776" text-anchor="middle">8 MB for the display, 56 MB spare</text>
          <text class="d-s" x="87" y="790" text-anchor="middle">&mdash; and 384 MB left to Linux</text>
''', '''          <text class="d-t" x="87" y="738" text-anchor="middle">1 GB LPDDR4</text>
''')
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
    svg = sub(svg, label, label + DE25_FIT_NOTE + fit_bars(DE25_FIT)
                   + slack_block('+1.663') + '\n')
    svg = sub(svg, '''">

          <rect class="d-box d-done d-key"''', '''">

%s          <rect class="d-box d-done d-key"''' % de25_comment())
    return svg

def build_de25():
    board_page('de25-nano.html', 'DE25-Nano', 'muir-fpga — the MIT CADR on a DE25-Nano',
               de25_description(),
               'QUUX and the CADR mapped onto one Altera Agilex 5 E-series, the A5EB013B.',
               "muir-fpga's board, waving",
               (('booting.html', 'How it boots'), ('debugging.html', 'The debug cable'),
                ('arty-z7-20.html', 'Arty Z7-20'), ('cora-z7-07s.html', 'Cora Z7-07S')),
               TERASIC_DE25, de25_svg())

DESC = {}
for _f in ('arty-z7-20.html', 'cora-z7-07s.html'):
    DESC[_f] = re.search(r'<meta name="description" content="([^"]*)">', open(os.path.join(BASE, _f)).read()).group(1)
DESC['cora-z7-07s.html'] = sub(DESC['cora-z7-07s.html'], 'where the two meet on the smaller part.', 'where the two meet.')
# The board runs the design, so it is not "proposed"; the words are the Cora
# Z7-07S's.
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
                  'Four sequences, two for the Zynq boards and two for the DE25-Nano: from the board&rsquo;s own card, which is how anybody else&rsquo;s board boots, and with TFTP, which is how this project&rsquo;s own boards boot while they are being worked on.',
                  body='<div class="hero-description">\n'
                       '<p>The two Zynq boards come up the same way as each other, so one drawing serves both. Where they differ, the drawing says so in a label.</p>\n'
                       '<p>The DE25-Nano has a pair of its own, because it boots differently enough to need one. Its boot crosses two storage devices rather than one, and its fabric is configured in the middle of the sequence rather than by the loader&rsquo;s first stage.</p>\n'
                       '<p>On either board the two paths differ only in where the files come from. The loader itself is read the same way on both, and the same last step ends both.</p>\n'
                       '</div>\n'))

    P.append(section('card', '01 / A ZYNQ BOARD, FROM ITS CARD', 'A Zynq board<br>on <em>its own.</em>',
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
             cls='fig dense', label='FIG. 01 &mdash; A ZYNQ BOARD, FROM ITS CARD', name='A Zynq board, from its card',
             more=more_line('The long form: %s.' % docs_link('the card, and the two ways it boots', 'boot.md', 'the-card-and-the-two-ways-it-boots')))))

    # THE DEVELOPMENT PATH IS NAMED FOR WHAT IT USES, on both boards and in the
    # same words: "with TFTP", and the parenthetical says what it is for.  The
    # two paths are then told apart by the thing that differs between them --- a
    # card or a server --- rather than by who happens to be using each.
    P.append(section('server', '02 / A ZYNQ BOARD, FOR DEVELOPMENT', 'A Zynq board<br>with <em>TFTP.</em>',
        'This project&rsquo;s own boards take the same five files from a TFTP server instead.',
        '''<div class="cols">
<p class="callout">A change to any of the board&rsquo;s five files is a copy on the server and a reset. Its card is never rewritten.</p>
<div class="prose"><p>The card&rsquo;s <code>uEnv.txt</code> decides between the two paths, by whether it names a server, and one U-Boot environment carries both. Each board&rsquo;s five files sit in a directory named for the board, and the network path never falls back to the card&rsquo;s own copies.</p></div>
</div>
''' + figure(s2, 'The two paths differ only in where the bytes come from: both put the CADR in the fabric before the kernel, and both end in the same <code>bootz</code>.',
             cls='fig dense', label='FIG. 02 &mdash; A ZYNQ BOARD, WITH TFTP', name='A Zynq board, with TFTP',
             more=more_line('The long form: %s.' % docs_link('one server, more than one board', 'boot.md', 'one-server-more-than-one-board')))))

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
        'This board takes the same two paths as the Zynq boards, and reaches them differently. There is no <code>BOOT.BIN</code>, because the first-stage loader is in the QSPI flash; and the fabric is empty until U-Boot fills it.',
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
             cls='fig dense', label='FIG. 03 &mdash; THE DE25-NANO, FROM ITS CARD', name='The DE25-Nano, from its card',
             more=more_line('The long form: %s.' % docs_link('the card, and the two ways it boots', 'boot.md', 'the-card-and-the-two-ways-it-boots')))))

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
    # its left are that one run's, as the two Zynq drawings' and the DE25 card
    # drawing's are of theirs.  The session is docs/board.md, "The DE25-Nano
    # over TFTP".
    P.append(section('de25-server', '04 / THE DE25-NANO, FOR DEVELOPMENT', 'The DE25-Nano<br>with <em>TFTP.</em>',
        'A change to any of the five served files is then a copy and a reset, and the card is never rewritten. This path has run on the board: 48,691,884 bytes over the network, and 28 seconds from the reset to the login prompt, against 25 off the card.',
        '''<div class="cols">
<p class="callout">The board&rsquo;s flash and card still carry its loader. Only the five files after it come from the server.</p>
<div class="prose"><p>The first-stage loader is in the QSPI flash, and it asks for <code>u-boot.itb</code> by that name at the root of the card, so neither of them comes from the server: the first stage reads the card, and it is U-Boot that speaks TFTP here. <code>uEnv.txt</code> is read off the card on this path too, and it is the file that chose the path. The four steps of the fabric&rsquo;s turn are the card path&rsquo;s own, and only the fetch before them changes.</p></div>
</div>
''' + figure(s4, 'The same board, the same flash and the same card, with a server in the middle. What the network changes is where the five files come from, and nothing else: the loader is still read off the card, and the boot ends in the same <code>booti</code>.',
             cls='fig dense', label='FIG. 04 &mdash; THE DE25-NANO, WITH TFTP', name='The DE25-Nano, with TFTP',
             more=more_line('The long form: %s.' % docs_link('one server, more than one board', 'boot.md', 'one-server-more-than-one-board'))),
        label='The DE25-Nano with TFTP, used for development'))
    page('booting.html', 'muir-fpga &mdash; booting',
         'How each board here comes up, in four sequences: a Zynq board and the DE25-Nano, each from its own microSD card, and each with TFTP while it is being worked on.',
         P)

# ================================================================ debugging

def build_debugging():
    base = open(os.path.join(BASE, 'debugging.html')).read()
    comment = re.search(r'<!-- THESE FIGURES CARRY NO BLOCK COLOR.*?-->', base, re.S).group(0)
    # fde is the DE25-Nano's connector, which sits between the cable and the
    # protocol in the base page and on the page, so the two names either side
    # of it keep pointing at the drawings they always did.
    f1, f2, f3, fde, f4, f5 = svgs('debugging.html')
    src_rows = open(os.path.join(HERE, 'dbg-src-rows.txt')).read()
    DC = 'debug-cable.md'
    P = [comment, '\n']
    P.append(hero('muir-fpga &middot; debugging', 'Debugging a<br>Lisp <em>Machine.</em>',
                  'A CADR is debugged by another CADR. This page is how MIT did that, and how a board here does it.',
                  body='<div class="hero-description">\n'
                       '<p>The debugger is not a program on a host. It is a second Lisp Machine, running bus cycles on the first over a cable of twenty-one wires, as though it were that machine&rsquo;s own processor.</p>\n'
                       '<p>The program that drives the cable is CC, and it is Lisp software on the debugging machine.</p>\n'
                       '<p>Every board here is a debuggee the moment it is powered, which is what a CADR is with nothing set, and one of them can be told to be the debugger instead.</p>\n'
                       '<p>The long form of every figure on this page is %s.</p>\n'
                       '</div>\n' % docs_link('docs/debug-cable.md', DC)))

    nfig = [0]
    def fig(svg, caption, title, more=''):
        nfig[0] += 1
        return figure(svg, caption, more=more, label='FIG. %02d &mdash; %s' % (nfig[0], title.upper()), name=title)

    # The heading carries the site's accent on its last words; the figure's
    # label is the same words without it.
    def plain(title):
        return re.sub(r'<[^>]+>', '', title.replace('<br>', ' '))

    def fig_section(n, sid, eyebrow, title, lead, svg, caption, links):
        more = more_line('The long form: %s.' % ', '.join(docs_link(t, p, a) for t, p, a in links))
        return section(sid, '%02d / %s' % (n - 1, eyebrow.upper()), title, lead, fig(svg, caption, plain(title).rstrip('.'), more))

    P.append(fig_section(2, 'mit', 'MIT&rsquo;s way', 'How MIT debugged<br>a <em>CADR.</em>',
        'The debugger&rsquo;s DBGOUT connector goes to the debuggee&rsquo;s DBGIN connector on its bus interface board, and a debugger works the cable by writing four registers of its own.',
        f1,
        'Every wire is held for the whole of a request, and the latches take the data at the trailing edge of their strobe. The <a href="../cadr/#cable">page on the real machine</a> has the four strobes and the connector they arrive on.',
        [('what crosses the cable', DC, 'what-crosses-the-cable')]))

    P.append(fig_section(3, 'fabric', 'On the boards', 'How the fabric<br><em>does it.</em>',
        'MIT&rsquo;s DBGIN logic is in the machine here, and so are the four DBGOUT registers CC writes, so a board can be either end of the cable.',
        f2,
        'Only the connector changes hands. A board&rsquo;s own DBGIN page is never switched off, so a debugger board stays debuggable through its window.',
        [('the window', DC, 'the-window'),
         ('every board is a debuggee', DC, 'every-board-is-a-debuggee-and-one-is-told-to-be-the-debugger')]))

    P.append(fig_section(4, 'cable', 'Between two boards', 'The <em>cable.</em>',
        'A cable for this link joins the eight signals and the two grounds, and leaves the 3.3 V supply pins open at both ends.',
        f3,
        'The connector is Pmod JA on both boards. A board told to be the debugger listens on both groups of pins first, so a ribbon made the wrong way up is found rather than trusted.',
        [('the cable on one connector of eight pins', DC, 'the-cable-on-one-connector-of-eight-pins'),
         ('the ribbon made the wrong way round', DC, 'the-ribbon-can-be-made-the-wrong-way-round-and-one-was')]))

    # THE DE25-NANO'S END, which is not a Pmod.  This section is where the
    # warning about the supply pins belongs: the front page carries it as a
    # line, and this is the page somebody reads with wire in their hand.  The
    # two things it has to say beyond the pin list are that the guards here
    # rest on a decision rather than on a schematic, and that no cable of this
    # shape exists, so nothing of this connector has been on hardware.
    P.append(section('de25', '04 / A GPIO HEADER, NOT A PMOD', 'The cable on<br>the <em>DE25-Nano.</em>',
        'That board has no Pmod, so its end of the cable is eight pins of a 2x20 GPIO header: JP1 pins 31 to 38, with the header&rsquo;s own ground on pin 30. The signals are on the odd pins and each guard is the even pin beside its signal.',
        '''<div class="cols">
<div class="prose">
<p><b>The guards here are a decision, not a measurement.</b> On the two Zynq boards the maker&rsquo;s schematics show the Pmod pins routed as coupled differential pairs, which is what a guard beside each signal is for. No schematic is published for this board and its manual says nothing about how JP1 is routed, so nothing is claimed about coupling between its pins 31 and 32.</p>
<p>The arrangement was carried across because it is what both other boards run, because somebody who knows one board should know this one, and because guards cost only frame length, which this cable has to spare. If a cable here ever misbehaves, that is the first assumption to revisit.</p>
</div>
<div>
<p class="callout">No cable of this shape exists. The far end is a Pmod, this end is a 2x20 header, and nobody has made the adapter.</p>
<div class="prose"><p>The connector is built, linted and read by a check, and it has crossed nothing. What has run on a real ribbon is the two Zynq boards, in the table below.</p></div>
</div>
</div>
''' + fig(fde,
          'The drawing answers the three questions somebody holding wire has: which of the board&rsquo;s two headers, which end of it, and which pins must never be joined. Pin 11 is 5 V and pin 29 is 3.3 V, and a cable joins neither &mdash; only the ground on pin 30. Neither supply pin is a fabric pin, so nothing in the design can drive one either.',
          'The cable on the DE25-Nano',
          more=more_line('The long form: %s.' % ', '.join(docs_link(t, DC, a) for t, a in (
              ('the DE25-Nano has no Pmod', 'the-de25-nano-has-no-pmod-so-its-connector-is-eight-of-jp1s-pins'),
              ('why each signal has a guard', 'the-pins-of-a-row-are-coupled-pairs-so-each-pair-carries-one-signal')))))))

    more = more_line('The long form: %s.' % ', '.join(docs_link(t, DC, a) for t, a in (
        ('twenty-four beats each way', 'twenty-four-beats-each-way'),
        ('what actually crosses', 'what-actually-crosses-counted-off-the-netlist'))))
    P.append(section('wire', '05 / FRAMES ON EIGHT PINS', 'The protocol<br>on the <em>wire.</em>',
        'Twenty-one wires do not fit on eight pins, so the levels cross as frames: four pins each way, and neither group is ever driven from both ends.',
        fig(f4, 'One signal to a pair of pins, the partner driven low as a guard: twenty-four beats, 162 ticks, a fraction of the 11.05 microseconds a debug cycle is allowed.', 'One frame, on the wire') +
        fig(f5, 'Twenty of MIT&rsquo;s signals cross one way and nineteen the other. The twenty-first bit each way is the carrier&rsquo;s own, and it is how two debuggees know neither is a debugger.', 'What crosses, each way', more=more)))


    rows = [
        ('The machine halted, and its registers read', 'CC through the register window, each register equal to the console&rsquo;s reading of the same halt', 'yes'),
        ('The scratchpads', 'CC&rsquo;s reads over the window, equal to the console&rsquo;s readout of the same words', 'yes'),
        ('Main memory, through the map', 'Words read through the mapped window, each equal to the console&rsquo;s reading of the same address; a write through the map moved MD and spent no microcycle', 'yes'),
        ('The ribbon between two boards', 'The role taken and given back on a real cable between two Pmod JA connectors, the far end answering', 'yes'),
        ('A mirrored ribbon, found by the fabric', 'The board told to connect reported the crossover it had found; forced the wrong way round, nothing answered', 'yes'),
        ('Two idle boards on that ribbon', 'Both read a debuggee with nothing driving the connector; the role bit removed the old lock-out', 'yes'),
        ('Neither machine noticing', 'Both boards ran Lisp throughout, at the rate they run at with no cable in them', 'yes'),
        ('CC over the ribbon', 'Halted, read and started again, both ways round, every word equal to the far board&rsquo;s own console and readout', 'yes'),
        ('Every microcycle accounted for', 'The far machine&rsquo;s cycle counter moved by one for each scratchpad read, and the debuggee&rsquo;s own window saw no request at all', 'yes'),
        ('The guards, and the frames refused', '0 refused in twenty-four readings, where the carrier before refused 163 and 185 in bursts; two frames on the other board are unaccounted for', 'yes'),
        ('A debug cycle over the carrier that runs now', 'A status read typed at the debugger&rsquo;s Listener, both ways round; no register of the far machine crossed', 'yes'),
        ('CC over the carrier that runs now', 'All sixteen of the far machine&rsquo;s diagnostic registers read over the guarded ribbon at one halt, each equal to the far board&rsquo;s own console, and the machine stepped and started over it; CC&rsquo;s own sequences typed at a Listener, and not the program run', 'yes'),
        ('A write over the ribbon', 'MD written over the ribbon by CC&rsquo;s own CC-WRITE-MD; the far board&rsquo;s own console read 0xa53c5ac3 where it read 0x0a0005c2 before and after the restore, and no microcycle was spent', 'yes'),
        ('The DE25-Nano&rsquo;s connector', 'Nothing. No cable from a 2x20 header to a Pmod has been made, so those eight pins have crossed nothing; what reads them is lint and a check on the pin map', 'not yet'),
    ]
    trs = ''.join('<tr><th scope="row">%s</th><td>%s</td><td class="st%s">%s</td></tr>\n'
                  % (a, b, '' if c == 'yes' else ' no', c) for a, b, c in rows)
    P.append(section('shown', '06 / ON SILICON', 'What has run<br>on a <em>board.</em>',
        'All three pieces have run on silicon: the window, the ribbon, and CC across the ribbon, both ways round. A write has crossed it since, into a register of the far machine rather than into its memory. CC itself ran on the earlier carrier, and what has crossed the guarded one is every cycle such a session is built out of.',
        '''<div class="table-scroll" tabindex="0" role="region" aria-label="What has run on a board"><table>
<thead><tr><th scope="col">What</th><th scope="col">How it was shown</th><th scope="col">Shown</th></tr></thead>
<tbody>
%s</tbody>
</table></div>
<p class="small-print"><code>yes</code> means a board itself has shown it, which is not the claim a board drawing&rsquo;s green makes: since the key was cut to three colors, green says a block is this project&rsquo;s work and done, which is built and checked rather than run on that board. Every reading, with its numbers, is in %s and %s.</p>
''' % (trs, docs_link('what two boards have shown', DC, 'what-two-boards-have-shown'),
       docs_link('the debugger over the cable', 'board.md', 'the-debugger-over-the-cable'))))

    P.append(section('sources', '07 / SOURCES', 'Where each drawing<br><em>came from.</em>',
        'Nothing above is a first-hand invention. A number with a leading <code>0o</code> is octal, which is how MIT writes an address.',
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
    P = [hero('muir-fpga &middot; the CADR', 'The CADR',
              'What the CADR is, board by board, is on its own page among the machines.',
              body='<p class="hero-description">muir-fpga puts it in the fabric of <a href="index.html#boards">three boards</a>; the drawings of the machine itself, read from MIT&rsquo;s own files, are on the CADR&rsquo;s page.</p>\n',
              keys=keys(('../cadr/', 'The CADR'), ('index.html', 'The boards')))]
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
     'Yes, while the grid and the tick are the same number: the microsecond clock counts 100 ticks, one real microsecond, and the vertical interrupt arrives at the display board&rsquo;s own 64.70 Hz.',
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
     'The GNU Affero General Public License, version 3 or later, apart from eight files compiled into U-Boot under the GPL, version 2 or later. The third-party material is on <a href="index.html#license">the boards page</a>.',
     '<code>docs/license.md</code>'),
  ]),
]

# Each group's eyebrow and heading, the heading with the site's accent.
FAQ_EYEBROW = tuple('%s QUESTIONS' % NUMBER[len(qs)].upper() for _, qs in FAQ)
FAQ_TITLE = ('The <em>machine.</em>', 'The boards, and the way<br>they are <em>checked.</em>')

def build_faq():
    import html as H
    base = open(os.path.join(BASE, 'faq.html')).read()
    comment = re.search(r'<!-- EVERY ANSWER HERE RESTS ON A FILE.*?-->', base, re.S).group(0)
    P = [comment, '\n']
    P.append(hero('muir-fpga &middot; questions', 'Questions',
                  'Questions this project is asked, each answered from the file that settles it.',
                  body='<p class="hero-description">Each answer here is a sentence or two; the whole of each is in %s. MIT&rsquo;s own files are cited at the path <a href="https://github.com/metebalci/muir-sim">muir-sim</a> gives them, and the rest are files here.</p>\n' % docs_link('docs/faq.md', 'faq.md')))
    # THE QUESTIONS ARE docs/faq.md's HEADINGS, word for word, because each
    # one's anchor there is made from its words; so a question keeps the
    # document's wording even where the site's would differ.  site_terms()
    # still renames a bare muir to muir-sim in the visible text of the other
    # questions, after the anchor is made from the document's own words.
    n = 1
    for group, qs in FAQ:
        cells = ''
        for q, a, src in qs:
            anchor = slug(H.unescape(q).replace('’', "'").replace('"', ''))
            cells += '''<div class="qa">
<h3>%s</h3>
<p>%s</p>
<p class="src">Rests on %s. %s.</p>
</div>
''' % (q.replace('"', '&ldquo;', 1).replace('"', '&rdquo;', 1), a, src, docs_link('The whole answer', 'faq.md', anchor))
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
    build_board('arty-z7-20.html', 'Arty Z7-20', 'QUUX and the CADR mapped onto one Xilinx Zynq 7020, the XC7Z020.', "muir-fpga's board, waving",
                ('cora-z7-07s.html', 'Cora Z7-07S'), DIGILENT_ARTY)
    build_board('cora-z7-07s.html', 'Cora Z7-07S', 'The CADR mapped onto one Xilinx Zynq 7007S, the XC7Z007S. This board builds the CADR alone; QUUX is built for the Arty Z7-20 and the DE25-Nano.', "muir-fpga's board, waving",
                ('arty-z7-20.html', 'Arty Z7-20'), DIGILENT_CORA)
    build_de25()
    build_booting()
    build_debugging()
    build_cadr()
    build_faq()
    return list(WRITTEN)

if __name__ == '__main__':
    main(sys.argv[1])
