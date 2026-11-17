.. _DevGuideDocumentation:

Documentation
=============

Qrisp's documentation is built with `Sphinx <https://www.sphinx-doc.org/>`_
and hosted at `qrisp.eu <https://www.qrisp.eu>`_. Contributions that add or
modify public functionality should include corresponding documentation updates.

Building the docs locally
--------------------------

All documentation source files live under ``documentation/source/``. To build
and preview them:

.. code-block:: bash

    # From the repository root
    cd documentation

    # One-shot build — output lands in documentation/build/html/
    make html

Open ``documentation/build/html/index.html`` in your browser to inspect the
result. Always verify that pages render correctly before submitting a pull
request — formatting that looks fine in raw reStructuredText may not render
well in Sphinx.

Documentation of all versions
-----------------------------

The website hosts the documentation of every release and of the development
version. ``qrisp.eu/en/latest/`` is built from ``main``, and
``qrisp.eu/en/<version>/``, for example ``qrisp.eu/en/0.9/``, from the git tag
of a release. ``qrisp.eu`` itself redirects to the newest release.

``make html`` builds only your checkout. To build the whole website into
``documentation/build/site``, run ``make versions``, which needs
`uv <https://docs.astral.sh/uv/>`_ and ``pandoc``. The workflow
``.github/workflows/docs_site.yml`` does the same on every push to ``main`` and
uploads the website as the artifact ``docs-site``. ``documentation/README.md``
explains how the versions are built.

When a new version is released, for example 0.10, add it to the website after
its git tag has been created:

#. Add a table ``[versions."0.10"]`` to ``documentation/versions/versions.toml``,
   following the comments in that file.
#. In ``documentation``, run ``python build_versions.py lock 0.10``. This pins the
   dependencies of the release in ``documentation/versions/0.10.lock``.
#. Set ``stable = "0.10"`` in ``documentation/versions/versions.toml``, so that
   ``qrisp.eu`` redirects to the new release.
#. Commit both files.

Docstrings
----------

Public functions and classes should have docstrings that use section headers
separated by dashes (``Parameters``, ``Returns``, ``Examples``, etc.),
following the `NumPy docstring style <https://numpydoc.readthedocs.io/en/latest/format.html>`_.
This is the pattern already used in the existing codebase.

Checklist for documentation contributions:

- All docstring ``Examples`` blocks execute correctly.
- New pages are registered in the appropriate ``index.rst`` ``toctree``.
- Cross-references (e.g., ``:ref:`QuantumFloat```) resolve without warnings.
- The build produces zero new Sphinx warnings.

Useful references
-----------------

- Sphinx documentation: https://www.sphinx-doc.org/
- NumPy docstring style: https://numpydoc.readthedocs.io/en/latest/format.html
- Google docstring style: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings
- reStructuredText primer: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
