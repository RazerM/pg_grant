# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from importlib.metadata import distribution

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pg_grant"
copyright = "2018, Frazer McLean"
author = "Frazer McLean"
release = distribution("pg_grant").version


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.inheritance_diagram",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_title = f"pg_grant documentation v{release}"
html_static_path = []


# -- Extension configuration -------------------------------------------------

# intersphinx
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "psycopg2": ("https://www.psycopg.org/docs/", None),
}

autodoc_member_order = "bysource"

napoleon_numpy_docstring = False

inheritance_graph_attrs = dict(bgcolor="transparent")
