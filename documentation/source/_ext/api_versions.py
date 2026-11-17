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

"""Label every documented object of the Qrisp API with the release that added it.

The table ``documentation/versions/api.json`` lists the names that the releases
define and, for each name, the first release that defines it. It is written by
``python build_versions.py api`` from the source code of the releases, see
``documentation/README.md``.

While Sphinx reads the docstrings, this extension inserts
``.. versionadded:: <release>`` after the summary of every documented object
that the oldest release in the table does not define yet. A method or another
member of a class is labeled only if it is newer than its class. Objects that
the source code being documented defines but no release does yet are labeled
with the upcoming release.

Names are compared without their module, for example ``QuantumVariable`` or
``QuantumArray.ravel``, so that an object that moved to another module keeps
the release that added it.

The functions above ``setup`` only use the standard library, because
``build_versions.py`` imports them without Sphinx being installed.
"""

import ast
import json
import tomllib
import warnings
from pathlib import Path

# Kinds of objects, as autodoc names them, that are labeled
MEMBERS = {"method", "classmethod", "staticmethod", "property", "attribute"}
TOP_LEVEL = {"class", "exception", "function", "decorator", "data"}

# Name of the development version in documentation/versions/versions.toml
DEV_VERSION = "latest"


def version_key(version):
    """Return a key that sorts version numbers such as "0.9" and "0.10" by age."""
    return tuple(int(part) for part in version.split("."))


def defined_names(code):
    """Return the names that the source code of a module defines.

    These are its classes and functions (``QuantumVariable``), its annotated
    variables such as type aliases, and the members of its classes
    (``QuantumArray.ravel``), including members assigned outside the class body
    (``BlockEncoding.svt = apply_svt``). Plain module-level variables are left
    out: example scripts assign names such as ``depth``, which would otherwise
    date functions of the same name.
    """
    with warnings.catch_warnings():
        # Older releases contain string escapes that newer Pythons warn about
        warnings.simplefilter("ignore", SyntaxWarning)
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return set()

    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
            if isinstance(node, ast.ClassDef):
                names.update(f"{node.name}.{member}" for member in _names_in_class(node))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, getattr(ast, "TypeAlias", ())):
            names.add(node.name.id)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                    names.add(f"{target.value.id}.{target.attr}")
    return names


def _names_in_class(node):
    """Yield the names of the methods, nested classes and attributes of a class."""
    for statement in node.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield statement.name
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            yield statement.target.id
        elif isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    yield target.id


def package_names(directory):
    """Return the names that the Python files below ``directory`` define."""
    names = set()
    for path in Path(directory).rglob("*.py"):
        names |= defined_names(path.read_bytes())
    return names


class ApiVersions:
    """The releases that added the names of the API, as needed while building."""

    def __init__(self, table, current_names, upcoming):
        self.first_release = table["first_release"]
        self.oldest = min(table["releases"], key=version_key)
        self.current_names = current_names
        self.upcoming = upcoming

    def release_of(self, name):
        """Return the release that added ``name``, or None if it is not known."""
        if name in self.first_release:
            return self.first_release[name]
        if name in self.current_names:
            return self.upcoming
        return None

    def label(self, what, name):
        """Return the release a documented object is labeled with, or None."""
        if not name.startswith("qrisp."):
            return None
        parts = name.split(".")
        if what in MEMBERS and len(parts) >= 3:
            added = self.release_of(".".join(parts[-2:]))
            owner = self.release_of(parts[-2])
            if added is None or owner is None or version_key(added) <= version_key(owner):
                return None
            return added
        if what in TOP_LEVEL:
            added = self.release_of(parts[-1])
            if added is None or added == self.oldest:
                return None
            return added
        return None


def upcoming_release(releases, version):
    """Return the version number of the next release.

    ``version`` is the version of the documented source code, such as "0.9" for
    the development version 0.9.10. It is the upcoming release if the table
    does not contain it yet, as for the source code of a release; otherwise the
    next minor version follows the newest release in the table.
    """
    newest = max(releases, key=version_key)
    if version_key(version) > version_key(newest):
        return version
    major, minor = version_key(newest)[:2]
    return f"{major}.{minor + 1}"


def insert_label(lines, release):
    """Insert ``.. versionadded:: <release>`` into the lines of a docstring.

    The label follows the summary, the first paragraph of the docstring. If
    that paragraph is not plain text, such as a directive or the introduction of
    a literal block, inserting the label there would separate it from its
    content. The label then precedes the first numpydoc section, such as
    ``Parameters``, or ends the docstring.
    """
    label = ["", f".. versionadded:: {release}", ""]
    start = next((index for index, line in enumerate(lines) if line.strip()), len(lines))
    end = next((index for index in range(start, len(lines)) if not lines[index].strip()), len(lines))
    following = next((line for line in lines[end:] if line.strip()), "")
    plain_summary = (
        start < end
        and not lines[start].lstrip().startswith("..")
        and not lines[end - 1].rstrip().endswith("::")
        and not _is_section(lines, start)
        and not following[:1].isspace()
    )
    if plain_summary:
        lines[end:end] = label
        return
    section = next((index for index in range(len(lines)) if _is_section(lines, index)), len(lines))
    lines[section:section] = label


def _is_section(lines, index):
    """Return whether a numpydoc section, such as ``Parameters``, starts at ``index``."""
    if index + 1 >= len(lines) or not lines[index].strip() or lines[index][:1].isspace():
        return False
    underline = lines[index + 1].strip()
    return len(underline) >= 3 and set(underline) == {"-"}


def setup(app):
    """Register the extension with Sphinx."""
    from sphinx.util import logging

    # Provides the event autodoc-process-docstring
    app.setup_extension("sphinx.ext.autodoc")
    logger = logging.getLogger(__name__)
    state = {}

    def load(app):
        docs_dir = Path(app.srcdir).parent
        table_file = docs_dir / "versions" / "api.json"
        if not table_file.exists():
            logger.warning(f"{table_file} is missing, so no object is labeled with the release that added it")
            return
        table = json.loads(table_file.read_text(encoding="utf-8"))

        manifest_file = docs_dir / "versions" / "versions.toml"
        if manifest_file.exists():
            with open(manifest_file, "rb") as file:
                listed = [version for version in tomllib.load(file)["versions"] if version != DEV_VERSION]
            missing = [version for version in listed if version not in table["releases"]]
            if missing:
                logger.warning(
                    f"versions/api.json lacks the releases {', '.join(missing)} of versions/versions.toml. "
                    "Run: python build_versions.py api"
                )

        current_names = package_names(docs_dir.parent / "src" / "qrisp")
        upcoming = upcoming_release(table["releases"], app.config.version)
        state["api"] = ApiVersions(table, current_names, upcoming)

    def label(app, what, name, obj, options, lines):
        if "api" in state:
            release = state["api"].label(what, name)
            if release is not None:
                insert_label(lines, release)

    app.connect("builder-inited", load)
    # Before numpydoc (priority 500) converts the docstring, so that the label
    # becomes part of its extended summary
    app.connect("autodoc-process-docstring", label, priority=400)
    return {"version": "1.0", "parallel_read_safe": True, "parallel_write_safe": True}
