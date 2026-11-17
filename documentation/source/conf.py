# ********************************************************************************
# * Copyright (c) 2026 the Qrisp authors
# *
# * This program and the accompanying materials are made available under the
# * terms of the Eclipse Public License 2.0 which is available at
# * http://www.eclipse.org/legal/epl-2.0.
# *
# * This Source Code may also be made available under the following Secondary
# * Licenses when the conditions for such availability set forth in the Eclipse
# * Public License, v. 2.0 are satisfied: GNU General Public License, version 2
# * with the GNU Classpath Exception which is
# * available at https://www.gnu.org/software/classpath/license.html.
# *
# * SPDX-License-Identifier: EPL-2.0 OR GPL-2.0 WITH Classpath-exception-2.0
# ********************************************************************************


# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import tomllib
import warnings

sys.path.insert(0, os.path.abspath("../../src/qrisp"))
sys.path.insert(0, os.path.abspath("_ext"))

# Treat Python warnings raised while building the docs as errors so that
# documentation regressions fail CI (Sphinx's ``-W`` only covers its own
# logger, not ``warnings.warn`` calls made by extensions such as numpydoc).
warnings.filterwarnings("error", message=r".*", category=UserWarning)
# numpydoc parses the raw docstring text and mistakes the dashed underline in
# printed circuit output (e.g. a "QuantumCircuit:" line inside a code block)
# for a section header, emitting a spurious "wrong underline length" warning.
# This is a false positive, so ignore it specifically.
warnings.filterwarnings(
    "ignore",
    message=r"potentially wrong underline length.*",
    category=UserWarning,
)
# os.fork() is flagged because JAX runs multiple threads; harmless here.
warnings.filterwarnings("ignore", message=r".*os\.fork.*", category=RuntimeWarning)

# -- Project information -----------------------------------------------------

project = ""
copyright = "2026, Qrisp developers"

# The version is read from the pyproject.toml of this checkout rather than from
# an installed ``qrisp`` package, so the documentation always states the version
# of the source it is built from. ``release`` is the full version ("0.9.10"),
# ``version`` its X.Y part ("0.9").
with open(os.path.abspath("../../pyproject.toml"), "rb") as _pyproject:
    release = tomllib.load(_pyproject)["project"]["version"]
version = ".".join(release.split(".")[:2])

# Shown in the title of every page. Without it Sphinx would build the title from
# the (empty) project name.
html_title = f"Qrisp {release} documentation"

# -- Multi-version documentation ---------------------------------------------

# The website hosts one build per released version plus one of the development
# version, each below https://qrisp.eu/en/<docs version>/. The build of the whole
# site sets QRISP_DOCS_VERSION to the URL segment of the version being built:
# "latest" for the development version, the release tag ("0.9") otherwise.
# Without the variable (``make html``, Read the Docs previews) a stand-alone
# build without version switcher is produced.
docs_version = os.environ.get("QRISP_DOCS_VERSION", "")


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.

extensions = [
    "nbsphinx",
    "sphinx.ext.autosummary",
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    # texext's math_dollar rewrites $...$ in docstrings/RST to :math:`...`; Sphinx core
    # (incl. sphinx.ext.mathjax) does not parse dollar-delimited math itself.
    "texext",
    "numpydoc",
    "sphinx_sitemap",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_thebe",
    "tutorial_authors",
]

# Configure sphinx-copybutton to only copy input lines (with >>> prompts) and strip the prompts
copybutton_prompt_text = r">>> |\.\.\. "
copybutton_prompt_is_regexp = True
# Only copy lines that have prompts (input lines), automatically excluding output
copybutton_only_copy_prompt_lines = True

# Use Python for default highlighting:
highlight_language = "python"

# Use a preferred Pygments style (e.g., "sphinx" or "monokai"):
pygments_style = "sphinx"

# Recognize code cells as Python 3 for highlighting:
nbsphinx_codecell_lexer = "ipython3"

imgmath_latex_preamble = r"\usepackage{braket}\n\usepackage{xcolor}"

thebe_config = {
    "repository_url": "https://github.com/fraunhoferfokus/Qrisp",
    "repository_branch": "thebe_branch",
    "selector": "div.input_area",
    "selector_output": "span.go",
}


imgmath_use_preview = True
# github_username = 'positr0nium'
github_repository = "https://github.com/eclipse-qrisp/Qrisp"

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "**/.ipynb_checkpoints",
]

# Map external documentation inventories so that cross-references to Python
# standard-library symbols (e.g. :exc:`RuntimeError`, :class:`~collections.abc.Mapping`)
# resolve to clickable links pointing at the official Python 3 documentation.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}
nbsphinx_timeout = 60

master_doc = "index"

# Root URL of this build. The trailing slash is required: canonical links and
# the sitemap append the page path to it.
html_baseurl = "https://qrisp.eu/"
if docs_version:
    html_baseurl += f"en/{docs_version}/"

# sphinx-sitemap prefixes every page path with the language and the version by
# default. html_baseurl already is the root of this build, so only the page path
# is appended.
sitemap_url_scheme = "{link}"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#


html_context = {
    # ...
    "default_mode": "light",
    # Used by the templates in _templates
    "docs_version": docs_version,
    "docs_baseurl": html_baseurl,
}


html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "announcement": (
        "🌟 Join us for the "
        '<a href="https://qrisp.eu/general/community_day.html">Eclipse Qrisp Community Day</a>'
        " on October 29th, 2026 in Berlin &mdash; "
        '<a href="https://luma.com/56k6pve5">register now</a>! 🌟'
    ),
    "collapse_navigation": True,
    "navigation_depth": 4,
    "show_prev_next": False,
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/eclipse-qrisp/Qrisp",
            "icon": "fab fa-github-square",
        },
    ],
    "navbar_start": ["navbar-logo"],
    "navbar_center": ["navbar-nav"],
    "navbar_end": ["navbar-icon-links"],
    "enable_search_shortcuts": True,
    "search_bar_text": "Search the docs... ",
    # "navbar_align": "content",
    "pygments_light_style": "lovelace",
    "secondary_sidebar_items": [
        "page-toc.html",
        "discord_link.html",
        "dynamic_sidebar.html",
        "thebe_button.html",
    ],
    "footer_start": ["copyright", "docs-version", "sphinx-version"],
}

if docs_version:
    # All builds share the versions.json at the root of the website, two levels
    # above the root of this build. It is written when the site is assembled, so
    # the theme cannot check it at build time.
    html_theme_options["switcher"] = {
        "json_url": "../../versions.json",
        "version_match": docs_version,
    }
    html_theme_options["check_switcher"] = False
    # Banner on every build other than the stable release
    html_theme_options["show_version_warning_banner"] = True
    # Next to the logo, the only place where the header has room left for it.
    # Narrow screens have no room there either, so a second copy is added to
    # navbar_end, whose items also appear in the navigation drawer.
    # version-switcher.css hides the copy that does not apply.
    html_theme_options["navbar_start"] = ["navbar-logo", "version-switcher"]
    html_theme_options["navbar_end"] = ["version-switcher", "navbar-icon-links"]

html_sidebars = {
    "**": ["sidebar-nav-bs"],
    "index": [],
    "install": [],
    "community_day": [],
    # "tutorial": [],
    "tutorial/*": ["sidebar-nav-bs"],
    "auto_examples/index": [],
}

autodoc_default_options = {
    "members": False,
    "member-order": "bysource",
    "special-members": None,
    "undoc-members": False,
    "exclude-members": None,
}
autosummary_generate = True
numpydoc_show_class_members = False

# Optional runtime dependencies that are documented but not part of the
# ``docs`` extra. Mock them so autodoc can import the wrapped modules without
# the real package installed (and without emitting import warnings).
autodoc_mock_imports = ["stim", "cudaq"]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# Removes the sphinx integrated option to see the page source
html_show_sourcelink = False

html_favicon = "../../logo/qrisp_favicon.png"

# html_logo = "../../logo/logo_extended.png"
html_logo = "../../logo/qrisp_logo.png"


add_module_names = False

html_css_files = [
    "css/custom09.css",
]
if docs_version:
    html_css_files.append("css/version-switcher.css")

source_suffix = [".rst"]
# Adds 'Edit on gitlab' in the upper right corner
# html_context = {
#     "display_gitlab": True, # Integrate Gitlab
#     "gitlab_repo": "Qrisp Compiler", # Repo name
#     "conf_py_path": "/source/", # Path in the checkout to the docs root
# }

html_extra_path = ["_extra"]  # copies contents of docs/_extra/ to _build/html/
