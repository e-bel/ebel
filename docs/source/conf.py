# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = 'e(BE:L)'
copyright = '2021, Christian Ebeling, Bruce Schultz'
author = 'Christian Ebeling, Bruce Schultz'

# The full version, including alpha/beta/rc tags
release = '1.0.11'

extensions = [
    'sphinx.ext.autodoc',  # Core Sphinx library for auto html doc generation from docstrings
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
    "sphinx_autodoc_typehints",  # Automatically document param types (less noise in class signature)
    'sphinx.ext.autosummary',  # Create neat summary tables for modules/classes/methods etc
    'sphinx_click.ext',
    'numpydoc',  # Parses docstrings that us numpy style
    'sphinxcontrib.openapi',  # For swagger file
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

language = None
pygments_style = 'sphinx'
todo_include_todos = False

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

numpydoc_show_class_members = False

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []
