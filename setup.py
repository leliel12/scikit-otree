#!/usr/bin/env python
# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) 2017 Juan BC

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


# =============================================================================
# DOCS
# =============================================================================

"""This file is for distribute scikit-otree

"""


# =============================================================================
# IMPORTS
# =============================================================================

import os

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup

os.environ["SKOTREE_IN_SETUP"] = "True"
import skotree


# =============================================================================
# CONSTANTS
# =============================================================================

REQUIREMENTS = [
    "otree-core>=1.4.18",
    "pyquery",
    "lxml",
    "pandas"]


with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as fp:
    README = fp.read()


# =============================================================================
# FUNCTIONS
# =============================================================================

def do_setup():
    setup(
        name=skotree.NAME,
        version=skotree.VERSION,
        description=skotree.DOC.splitlines()[0],
        long_description=README,
        author=skotree.AUTHORS,
        author_email=skotree.EMAIL,
        url=skotree.URL,
        license=skotree.LICENSE,
        keywords=skotree.KEYWORDS,
        classifiers=(
            "Development Status :: 4 - Beta",
            "Intended Audience :: Education",
            "Intended Audience :: Science/Research",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            "Programming Language :: Python :: Implementation :: CPython",
            "Topic :: Scientific/Engineering",
        ),
        py_modules=["ez_setup", "skotree"],
        install_requires=REQUIREMENTS)


if __name__ == "__main__":
    do_setup()
