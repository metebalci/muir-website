# SPDX-License-Identifier: AGPL-3.0-or-later
"""The site's chrome: the head, the header with the Lisp Machine pages
and the four projects, a section's own page list, and the footer.  Every page but the two
full-size image pages is wrapped in it, by gen/build.py for the pages
written by hand in src/ and by gen/fpga/gen.py for muir-fpga's."""

GH = 'https://github.com/metebalci/'

# The four projects, in the order the site lists them, each with its path,
# its label in the header and its repository.  muir-sim's repository is
# still github.com/metebalci/muir until it is renamed.
SECTIONS = [
    ('simulator', 'Simulator', 'muir-sim', GH + 'muir'),
    ('fpga', 'FPGA', 'muir-fpga', GH + 'muir-fpga'),
    ('system', 'System', 'muir-sys', GH + 'muir-sys'),
    ('ozd', 'ozd', 'ozd', GH + 'ozd'),
]

# The pages about the Lisp Machine itself, what it is and how it runs:
# the site's own, not a project's, so the header lists it before the
# projects and the footer, which lists the projects, does not.
GUIDE = ('lisp-machine', 'Lisp Machine', 'The Lisp Machine')

# A section's own pages, in one fixed order, so that no word moves as a
# reader goes from page to page.
SUBNAV = {
    'lisp-machine': [('index.html', 'What it is'), ('how-it-runs.html', 'How it runs')],
    'simulator': [('index.html', 'The simulator'), ('quux.html', 'QUUX')],
    'fpga': [('index.html', 'The boards'), ('arty-z7-20.html', 'Arty Z7-20'),
             ('cora-z7-07s.html', 'Cora Z7-07S'), ('de25-nano.html', 'DE25-Nano'),
             ('booting.html', 'Booting'), ('debugging.html', 'Debugging'),
             ('faq.html', 'Questions'), ('cadr.html', 'The CADR')],
    'system': [('index.html', 'The system'), ('releases.html', 'Release notes')],
}


def root_of(path):
    """The relative way back to the site's root from a page at `path`,
    which is relative to pages/.  The 404 page is served at any depth, so it
    alone links from the root itself."""
    if path == '404.html':
        return '/'
    return '../' * path.count('/')


def href(root, target):
    """A link to `target`, a path relative to the site's root."""
    if target == 'index.html':
        return root if root else './'
    return root + target


def header(root, section):
    items = []
    for sid, label, _, _ in (GUIDE + (None,),) + tuple(SECTIONS):
        cur = ' aria-current="page"' if sid == section else ''
        items.append('<a href="%s"%s>%s</a>' % (href(root, sid + '/'), cur, label))
    repo = dict((s[0], s[3]) for s in SECTIONS).get(section, GH + 'muir-website')
    return ('<a class="skip" href="#main">Skip to content</a>\n'
            '<header class="header wrap"><a class="wordmark" href="%s" aria-label="muir, the front page">muir<span>&#8599;</span></a>'
            '<span class="header-note">CADR PRESERVED.<br>QUUX EVOLVED.</span>'
            '<nav aria-label="The site&rsquo;s sections">%s<a class="github" href="%s">GitHub <span>&#8599;</span></a></nav></header>\n'
            % (href(root, 'index.html'), ''.join(items), repo))


def subnav(section, current):
    pages = SUBNAV.get(section)
    if not pages:
        return ''
    name = dict([(GUIDE[0], GUIDE[2])] + [(s[0], s[2]) for s in SECTIONS])[section]
    out = []
    for fname, label in pages:
        if fname == current:
            out.append('<span aria-current="page">%s</span>' % label)
        else:
            out.append('<a href="%s">%s</a>' % ('./' if fname == 'index.html' else fname, label))
    return '<nav class="subnav wrap" aria-label="%s&rsquo;s pages"><b>%s</b>%s</nav>\n' % (name, name, ''.join(out))


def footer(root):
    links = ''.join('<a href="%s">%s &middot; %s</a>' % (href(root, sid + '/'), name, label)
                    for sid, label, name, _ in SECTIONS)
    return ('<footer class="wrap footer"><div class="footer-top"><a class="wordmark" href="%s" aria-label="muir, the front page">muir<span>&#8599;</span></a>'
            '<div class="footer-copy"><p>CADR preserved.<br>QUUX evolved.</p>'
            '<p class="credit">The site is designed with Codex, using OpenAI&rsquo;s GPT Astra, and with '
            '<a href="https://claude.com/claude-code">Claude Code</a>, using Anthropic&rsquo;s Claude Opus. '
            'Its source is <a href="%s">muir-website</a>.</p></div>'
            '<div>%s<a href="%smuir/blob/main/docs/sources.md">Sources &amp; acknowledgments &#8599;</a></div></div>'
            '<div class="footer-bottom mono"><span>&copy; 2026 METE BALCI / AGPL-3.0-OR-LATER</span>'
            '<a href="#main">BACK TO TOP &#8593;</a></div></footer>\n'
            % (href(root, 'index.html'), GH + 'muir-website', links, GH))


def page(path, title, description, main, section=None, css=(), script=False, body_class=None, current=None):
    """A whole page.  `path` is relative to pages/, `main` is what goes
    inside <main>, and `css` names extra stylesheets at the root, such as
    'drawings.css'."""
    root = root_of(path)
    links = ''.join('<link rel="stylesheet" href="%s">\n' % href(root, c) for c in ('style.css',) + tuple(css))
    js = '<script src="%s" defer></script>\n' % href(root, 'script.js') if script else ''
    cls = ' class="%s"' % body_class if body_class else ''
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n%s%s</head>\n<body%s>\n'
            '%s%s<main id="main">\n%s</main>\n%s</body>\n</html>\n'
            % (title, description, links, js, cls, header(root, section),
               subnav(section, current or path.rsplit('/', 1)[-1]) if section else '',
               main, footer(root)))
