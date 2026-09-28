# muir-website

The website of the muir projects, published at <https://muir.metebalci.com/>.

Project muir is to simulate MIT's CADR Lisp Machine accurately, and to create
an evolved version of it, QUUX. The site has a front page and a section for
each of its four projects, each project's pages directly under its path:

| Path | Project | Repository |
|---|---|---|
| `/` | the front page: the aim, the two machines, the four projects | this one |
| `/lisp-machine/` | what a Lisp Machine is, and how its system runs | this one |
| `/simulator/` | muir-sim, the simulator of the CADR and QUUX | [metebalci/muir-sim](https://github.com/metebalci/muir-sim) |
| `/fpga/` | muir-fpga, the machines in the fabric of FPGA boards | [metebalci/muir-fpga](https://github.com/metebalci/muir-fpga) |
| `/system/` | muir-sys, the Lisp Machine system | [metebalci/muir-sys](https://github.com/metebalci/muir-sys) |
| `/ozd/` | ozd, the CADR's associated machine | [metebalci/ozd](https://github.com/metebalci/ozd) |

## The tree

    pages/        the published tree, deployed as it stands. Its HTML is
                  built (below) and committed; style.css, drawings.css,
                  script.js, fonts/ and the images are written by hand
    src/          the pages written by hand: what goes inside <main>, after a
                  comment of key: value lines giving the title, description
                  and what else the page loads
    gen/build.py  builds every page into pages/
    gen/chrome.py the head, the header with the four projects, a section's
                  page list and the footer, shared by every page
    gen/fpga/     muir-fpga's pages: gen.py writes them from the drawings in
                  base/, which it lifts byte for byte; checks/ holds its
                  geometric checks of the drawings (checks/runall.sh
                  pages/fpga gen/fpga/base)
    checks/       the site's checks, below
    .github/workflows/pages.yml
                  runs the checks and deploys pages/ to GitHub Pages

Build after any change to `src/` or `gen/`, and commit what it writes:

    python3 gen/build.py

To look at it, serve `pages/`:

    python3 -m http.server --bind 0.0.0.0 --directory pages 8000

## The checks

Each runs locally and in `pages.yml`, and each has been shown to fail on a
fault planted for it.

    python3 checks/generated.py      pages/ is what gen/build.py writes
    python3 checks/links.py --repos DIR
                                     every internal link and #anchor
                                     resolves; with --repos, a directory of
                                     clones of the four projects, so does
                                     every link into their files, headings
                                     and release tags on GitHub
    python3 checks/public.py         no local path, private address, local
                                     port, process ID, e-mail address,
                                     session, or this machine's or user's
                                     name in the public tree
    python3 checks/fonts.py          every character drawn in one of the
                                     site's fonts, Plex, Zen Maru Gothic or
                                     Gelasio, where it is the first family
                                     named, is in that font's files; needs
                                     Chromium or Chrome and fc-query
                                     (fontconfig)
    python3 checks/sitelinks.py --repos DIR
                                     every muir.metebalci.com link and
                                     #anchor in the four projects' tracked
                                     files resolves on the site, and none
                                     names a retired site
    python3 checks/test_checks.py --repos DIR
                                     plants a fault for each check in a
                                     scratch copy and requires it to fail

## License

The site's own work --- its pages, stylesheets, script, generator and
checks --- is free software under the GNU Affero General Public License,
version 3 or later; the full text is [`LICENSE`](LICENSE). The drawings are
the projects' own work, under the same license.

The fonts are not this project's work. IBM Plex Mono (regular and medium),
by IBM, Zen Maru Gothic (medium and bold), by the Zen Maru Gothic Project
Authors, and Gelasio (italic), by the Gelasio Project Authors, are under the
SIL Open Font License, Version 1.1, whose texts are beside them in
`pages/fonts/`. The IBM Plex Mono files are Google Fonts' own `latin`
subset, unmodified: Plex is licensed with the Reserved Font Name "Plex", so
it is never cut here. The Zen Maru Gothic files are subsets cut from the
upstream TTFs in [google/fonts](https://github.com/google/fonts); the
drawings' labels were placed in them. The Gelasio file is cut from the
upstream variable italic TTF there, at weight 400, to the range of Google
Fonts' `latin` subset; Gelasio has no Reserved Font Name. The headings'
italic accents are set in Georgia, and in Gelasio, metrically compatible
with Georgia, where the reader's system has no Georgia.

## How it was written

The site is designed with Codex, using OpenAI's GPT Astra, and with [Claude Code](https://claude.com/claude-code), using Anthropic's Claude Opus.
