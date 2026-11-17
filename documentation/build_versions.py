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

"""Build the Qrisp documentation of every version and assemble the website.

The website hosts one build of the documentation per released version and one of
the development version, each below ``https://qrisp.eu/en/<version>/``. The
versions are listed in ``versions/versions.toml``.

Usage, from the ``documentation`` directory::

    python build_versions.py build             # build all versions, then assemble
    python build_versions.py build latest 0.9  # build only these versions, then assemble
    python build_versions.py assemble          # only write the files shared by all versions
    python build_versions.py lock 0.10         # pin the dependencies of a release

The website is written to ``build/site``. Building requires ``uv`` and ``pandoc``.
See ``README.md`` for details.
"""

import argparse
import configparser
import io
import json
import os
import posixpath
import shutil
import subprocess
import tarfile
import tomllib
from pathlib import Path
from urllib.parse import quote

DOCS_DIR = Path(__file__).resolve().parent
REPO_DIR = DOCS_DIR.parent
VERSIONS_DIR = DOCS_DIR / "versions"

# The two constants below must match source/conf.py.
# Root of the website. A version is hosted at SITE_URL + "en/<version>/".
SITE_URL = "https://qrisp.eu/"
# Name of the development version in URLs and in versions.toml
DEV_VERSION = "latest"

# Settings appended to the conf.py of a release that predates the multi-version
# settings of source/conf.py. They do for that release what conf.py does when
# QRISP_DOCS_VERSION is set.
LEGACY_SETTINGS = """

# -- Appended by documentation/build_versions.py -----------------------------
release = {release!r}
version = ".".join(release.split(".")[:2])
html_title = f"Qrisp {{release}} documentation"
html_baseurl = {baseurl!r}
sitemap_url_scheme = "{{link}}"
html_theme_options = dict(html_theme_options)
html_theme_options["switcher"] = {{"json_url": "../../versions.json", "version_match": {version!r}}}
html_theme_options["check_switcher"] = False
html_theme_options["show_version_warning_banner"] = True
html_theme_options["navbar_start"] = ["navbar-logo", "version-switcher"]
html_theme_options["navbar_end"] = ["version-switcher", *html_theme_options["navbar_end"]]
html_theme_options["footer_start"] = ["copyright", "docs-version", "sphinx-version"]
html_css_files = [*html_css_files, "css/version-switcher.css"]


def _add_version_meta(app, pagename, templatename, context, doctree):
    context["metatags"] = context.get("metatags", "") + f'<meta name="docsearch:version" content="{{release}}" />\\n'


_setup_of_release = globals().get("setup")


def setup(app):
    app.connect("html-page-context", _add_version_meta)
    if _setup_of_release is not None:
        return _setup_of_release(app)
"""

# Page written to the former location of a page, see write_redirects
REDIRECT = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Redirecting to the Qrisp {version} documentation</title>
    <link rel="canonical" href="{canonical}">
    <meta name="robots" content="noindex">
    <script>window.location.replace("{target}" + window.location.search + window.location.hash);</script>
    <meta http-equiv="refresh" content="0; url={target}">
  </head>
  <body>
    <p>This page has moved to <a href="{target}">{canonical}</a>.</p>
  </body>
</html>
"""


def run(*command, **kwargs):
    """Print a command, run it and fail if it fails."""
    command = [str(part) for part in command]
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, check=True, **kwargs)


def load_manifest():
    """Read ``versions/versions.toml``."""
    with open(VERSIONS_DIR / "versions.toml", "rb") as file:
        return tomllib.load(file)


def lock_file(version):
    """Return the path of the file pinning the dependencies of a release."""
    return VERSIONS_DIR / f"{version}.lock"


def export_source(version, spec, source):
    """Write a copy of the source of a version to the directory ``source``.

    The documentation is never built inside the checkout: Sphinx regenerates the
    autosummary pages, which are tracked by git, and the conf.py of older
    releases is extended, see ``prepare``.
    """
    if version == DEV_VERSION:
        # The checkout as it is, including changes that are not committed
        for name in ("documentation", "src", "logo"):
            ignored = shutil.ignore_patterns("build", "__pycache__", ".ipynb_checkpoints")
            shutil.copytree(REPO_DIR / name, source / name, ignore=ignored)
        shutil.copy2(REPO_DIR / "pyproject.toml", source)
    else:
        tag = spec.get("tag", version)
        archive = subprocess.run(
            ["git", "-C", str(REPO_DIR), "archive", "--format=tar", tag], check=True, stdout=subprocess.PIPE
        )
        with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
            tar.extractall(source, filter="data")


def release_of(source):
    """Return the full version number of the Qrisp package in ``source``."""
    with open(source / "pyproject.toml", "rb") as file:
        project = tomllib.load(file).get("project", {})
    if "version" in project:
        return project["version"]
    # The releases up to 0.8 declare it in setup.cfg
    setup_cfg = configparser.ConfigParser()
    setup_cfg.read(source / "setup.cfg", encoding="utf-8")
    return setup_cfg["metadata"]["version"]


def lock(version, spec, work):
    """Pin the dependencies of a release in ``versions/<version>.lock``."""
    if "resolved" not in spec:
        raise SystemExit(f"{version}: only releases with a 'resolved' date in versions.toml have a lock file")
    directory = work / version
    if directory.exists():
        shutil.rmtree(directory)
    export_source(version, spec, directory / "source")

    # The release declares its dependencies in pyproject.toml or, up to 0.8, in
    # setup.py. Paths are relative so that the lock file reads the same on every machine.
    with open(directory / "source" / "pyproject.toml", "rb") as file:
        inputs = ["source/pyproject.toml" if "project" in tomllib.load(file) else "source/setup.py"]
    (directory / "packages.in").write_text("\n".join(spec.get("packages", [])) + "\n", encoding="utf-8")
    inputs.append("packages.in")
    extras = [option for extra in spec.get("extras", []) for option in ("--extra", extra)]
    command = ["uv", "pip", "compile", *inputs, *extras]
    command += ["--python-version", spec["python"], "--exclude-newer", spec["resolved"]]
    # Pins that are valid on every platform, not only on the one running this command
    command += ["--universal"]
    command += ["--custom-compile-command", f"python build_versions.py lock {version}"]
    command += ["--output-file", lock_file(version)]
    run(*command, cwd=directory)


def prepare(version, spec, source):
    """Adapt the copied source of a version to the multi-version website."""
    docs_source = source / "documentation" / "source"
    conf = docs_source / "conf.py"
    settings = conf.read_text(encoding="utf-8")

    if "QRISP_DOCS_VERSION" not in settings:
        # A release that predates the multi-version settings of conf.py
        settings += LEGACY_SETTINGS.format(
            version=version, release=release_of(source), baseurl=f"{SITE_URL}en/{version}/"
        )
        shutil.copy2(DOCS_DIR / "source" / "_static" / "css" / "version-switcher.css", docs_source / "_static" / "css")
        shutil.copy2(DOCS_DIR / "source" / "_templates" / "docs-version.html", docs_source / "_templates")
        # Releases 0.8 and 0.9 link the notebook of a tutorial from the root of the website
        sidebar = docs_source / "_templates" / "dynamic_sidebar.html"
        if sidebar.exists():
            template = sidebar.read_text(encoding="utf-8")
            template = template.replace('href="/{{ pagename }}.ipynb"', "href=\"{{ pathto(pagename + '.ipynb', 1) }}\"")
            sidebar.write_text(template, encoding="utf-8")

    if not spec.get("execute_notebooks", True):
        settings += '\nnbsphinx_execute = "never"\n'
    conf.write_text(settings, encoding="utf-8")


def create_environment(version, spec, source, venv):
    """Create the build environment of a version and return its Python interpreter."""
    run("uv", "venv", "--python", spec["python"], venv)
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    install = ("uv", "pip", "install", "--python", python)
    if version == DEV_VERSION:
        extras = [option for extra in spec.get("extras", []) for option in ("--extra", extra)]
        run(*install, "-r", source / "pyproject.toml", *extras)
    else:
        if not lock_file(version).exists():
            raise SystemExit(f"{lock_file(version)} is missing, run: python build_versions.py lock {version}")
        run(*install, "-r", lock_file(version))
    for requirements in spec.get("no_deps", []):
        run(*install, "--no-deps", "-r", source / requirements)
    return python


def build(version, spec, work, output):
    """Build the documentation of a version into ``<output>/en/<version>``."""
    directory = work / version
    destination = output / "en" / version
    for stale in (directory, destination):
        if stale.exists():
            shutil.rmtree(stale)

    source = directory / "source"
    export_source(version, spec, source)
    prepare(version, spec, source)
    python = create_environment(version, spec, source, directory / "venv")

    environment = dict(os.environ)
    environment["QRISP_DOCS_VERSION"] = version
    # The package is imported from the copied source instead of being installed
    environment["PYTHONPATH"] = str(source / "src")
    environment["PATH"] = os.pathsep.join([str(python.parent), environment["PATH"]])
    # Like `make html`, the development version fails on warnings. Releases do
    # not: their sources cannot be fixed anymore.
    options = ["-W", "--keep-going"] if version == DEV_VERSION else []
    # -d keeps Sphinx's cache out of the website
    options += ["-d", directory / "doctrees"]
    run(
        python,
        "-m",
        "sphinx",
        "-b",
        "html",
        *options,
        source / "documentation" / "source",
        destination,
        env=environment,
    )


def write_redirects(output, versions):
    """Write a redirecting page to every former location of a page.

    Before the website hosted several versions, the pages were located at its
    root. Each of these locations redirects to the same page of the first of
    ``versions`` that has it.
    """
    written = set()
    for version in versions:
        root = output / "en" / version
        for page in sorted(root.rglob("*.html")):
            location = page.relative_to(root).as_posix()
            if location in written or location.startswith("_static/"):
                continue
            written.add(location)
            moved_to = f"en/{version}/{location}"
            redirect = REDIRECT.format(
                version=version,
                canonical=SITE_URL + quote(moved_to),
                target=quote(posixpath.relpath(moved_to, posixpath.dirname(location) or ".")),
            )
            (output / location).parent.mkdir(parents=True, exist_ok=True)
            (output / location).write_text(redirect, encoding="utf-8")
    return len(written)


def assemble(manifest, output):
    """Write the files shared by all versions to the root of the website."""
    built = [version for version in manifest["versions"] if (output / "en" / version / "index.html").exists()]
    stable = manifest["stable"]

    # The entries of the version switcher, see the documentation of the theme:
    # https://pydata-sphinx-theme.readthedocs.io/en/stable/user_guide/version-dropdown.html
    switcher = []
    for version in built:
        entry = {"name": version, "version": version, "url": f"/en/{version}/"}
        if version == DEV_VERSION:
            entry["name"] = f"{release_of(REPO_DIR)} (dev)"
        elif version == stable:
            entry["name"] = f"{version} (stable)"
            # Every other version shows a banner that links to this one
            entry["preferred"] = True
        switcher.append(entry)
    output.mkdir(parents=True, exist_ok=True)
    (output / "versions.json").write_text(json.dumps(switcher, indent=2) + "\n", encoding="utf-8")
    print(f"versions.json lists: {', '.join(built) or 'no version'}")

    if stable in built:
        # Pages that the stable release does not have yet redirect to the development version
        count = write_redirects(output, [version for version in (stable, DEV_VERSION) if version in built])
        print(f"{count} redirects written, the root of the website redirects to {stable}")
    else:
        print(f"No redirects written: the stable version {stable} is not built")

    # Files that must be located at the root of the website, such as the
    # verification file of the Google Search Console
    for file in (DOCS_DIR / "source" / "_extra").iterdir():
        if file.is_file():
            shutil.copy2(file, output)


def main():
    """Run the command given on the command line."""
    parser = argparse.ArgumentParser(description="Build the Qrisp documentation of every version.")
    parser.add_argument("--output", type=Path, default=DOCS_DIR / "build" / "site", help="directory of the website")
    parser.add_argument(
        "--work", type=Path, default=DOCS_DIR / "build" / "versions", help="directory for sources and environments"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name, description in (
        ("build", "build the given versions (default: all) and assemble the website"),
        ("lock", "pin the dependencies of the given releases (default: all)"),
    ):
        command = commands.add_parser(name, help=description)
        command.add_argument("versions", nargs="*", help="versions listed in versions/versions.toml")
    commands.add_parser("assemble", help="write the files shared by all versions")
    arguments = parser.parse_args()

    manifest = load_manifest()
    output, work = arguments.output.resolve(), arguments.work.resolve()
    if arguments.command == "assemble":
        assemble(manifest, output)
        return

    unknown = [version for version in arguments.versions if version not in manifest["versions"]]
    if unknown:
        raise SystemExit(f"Not listed in versions/versions.toml: {', '.join(unknown)}")
    required = ["uv", "pandoc"] if arguments.command == "build" else ["uv"]
    missing = [tool for tool in required if shutil.which(tool) is None]
    if missing:
        raise SystemExit(f"Not found on the PATH: {', '.join(missing)}. See README.md.")

    if arguments.command == "lock":
        releases = [version for version in manifest["versions"] if version != DEV_VERSION]
        for version in arguments.versions or releases:
            lock(version, manifest["versions"][version], work)
    else:
        for version in arguments.versions or manifest["versions"]:
            build(version, manifest["versions"][version], work, output)
        assemble(manifest, output)


if __name__ == "__main__":
    main()
