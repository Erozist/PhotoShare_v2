# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import sys
import os
from pathlib import Path
project = 'PHOTOSHARE'
copyright = '2024, project_group_6'
author = 'project_group_6'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

current_dir = os.path.dirname(__file__)
src_dir = os.path.abspath(os.path.join(current_dir, "../../src"))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.insert(0, src_dir)
sys.path.insert(0, project_root)

extensions = ['sphinx.ext.autodoc']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'nature'
html_static_path = ['_static']
