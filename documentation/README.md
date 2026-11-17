# Documentation for qrisp project
This README gives an overview of the relevant files of the documentation page development.\
The documentation is build with sphinx. For further information I recommend the following tutorial:\
[How to Document using Sphinx: Part 1—Setting up](https://www.youtube.com/watch?v=WcUhGT4rs5o)

# Running the documentation server for preview
Using sphinx-autobuild package, you can run a local server to preview the documentation page.

To run the live server, navigate to the documentation folder and use the following command:
```bash
    sphinx-autobuild source build/html --open-browser
```

# Setup page    
Every page of the documentation website is designed in the related .rst file inside the source folder.\
Each page needs to be integrated via index.rst file.\
Of further interest is the conf.py, check out the recommended tutorial for its functionality.

# Creating the actual html page
```bash
    make docs-install
    make html
```
The `make docs-install` command installs the Python documentation requirements
and the `pandoc` system package. The `make html` command generates the html
pages inside the build/html folder.\
Opening the index.html file in the browser displays the build version of the documentation page.

# Building the documentation of all versions
The website hosts one build of the documentation per released version and one of
the development version:

| URL | Version |
| --- | --- |
| `https://qrisp.eu/en/latest/` | development version, built from `main` |
| `https://qrisp.eu/en/0.9/` | release 0.9, and likewise for every other release |

`https://qrisp.eu/` redirects to the newest release. Every page has a version
switcher, and every version other than the newest release shows a banner that
links to it.

`make html` builds only the checkout, without the version switcher. The whole
website is built by `build_versions.py`:
```bash
    make versions                               # all versions
    python build_versions.py build latest 0.9   # only these versions
```
The script needs [uv](https://docs.astral.sh/uv/), which provides the Python
version and the environment of each version, and `pandoc`. It writes the website
to build/site. The version switcher only works when the website is served, so
preview it with:
```bash
    python -m http.server --directory build/site
```

How it works:
- `versions/versions.toml` lists the versions and how each one is built.
- A release is built from its git tag, in its own environment. Its dependencies
  are pinned in `versions/<version>.lock`, as they were when it was released.
- The development version is built from the checkout, with the dependencies of
  `make docs-install`. Like `make html` it fails on warnings; releases do not.
- Nothing is built inside the checkout. The script works on copies in
  build/versions.
- Sphinx learns which version it builds from the environment variable
  `QRISP_DOCS_VERSION`, which `source/conf.py` reads. The releases up to 0.9 do
  not read it yet, so the script appends the settings to the copy of their
  `conf.py`.
- At the root of the website the script writes `versions.json` for the version
  switcher, the files of `source/_extra`, and a page that redirects to the
  newest release at every location a page had before the website hosted several
  versions.

## Adding a release
After tagging a release, for example 0.10:
1. Add a table `[versions."0.10"]` to `versions/versions.toml`, following the
   comments there.
2. Run `python build_versions.py lock 0.10` and commit `versions/0.10.lock`.
3. Set `stable = "0.10"` in `versions/versions.toml`.