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
# DOCS & META
# =============================================================================

"""oTree integration to the scientific Python Stack

Based on:

    Chen, D. L., Schonger, M., & Wickens, C. (2016).
    oTree-An open-source platform for laboratory, online, and field
    experiments.
    Journal of Behavioral and Experimental Finance, 9, 88-97.

"""

import os

__version__ = ("0", "2", "1")

__all__ = ["oTree"]

NAME = "scikit-otree"

DOC = __doc__

VERSION = ".".join(__version__)

AUTHORS = "Juan BC"

EMAIL = "jbc.develop@gmail.com"

URL = "https://github.com/leliel12/scikit-otree"

LICENSE = "MIT License"

KEYWORDS = "mcda mcdm ahp moora muti criteria".split()


# =============================================================================
# IMPORTS
# =============================================================================

import contextlib
import io
import pickle
import multiprocessing as mp
from unittest import mock

if os.getenv("SKOTREE_IN_SETUP") != "True":
    import pandas as pd


# =============================================================================
# CONTEXT
# =============================================================================

@contextlib.contextmanager
def cd(path):
    old_path = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_path)


class oTreeContextProcess(mp.Process):

    def __init__(self, path, func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._path = path
        self._func = func
        self._queue = mp.Queue()

    def __repr__(self):
        return "oTree@{}$ {}".format(self._path, self._func)

    def run(self):
        result = io.BytesIO()
        with cd(self._path):
            with mock.patch("sys.stdout"), mock.patch("warnings.warn"):
                from otree.management import cli
                cli.otree_cli()
            result = self._func()
        serialized = pickle.dumps(result)
        self._queue.put(serialized)

    def get_result(self):
        serialized = self._queue.get()
        result = pickle.loads(serialized)
        return result

    @property
    def path(self):
        return self._path


class oTree(object):

    def __init__(self, path):
        self._path = os.path.abspath(path)
        self._settings = self._from_path_settings()

    def __repr__(self):
        """x.__repr__() <==> repr(x)"""
        return "<oTree@{}>".format(self._path)

    def _execute(self, func):
        cmd = oTreeContextProcess(self._path, func)
        cmd.start()
        cmd.join()
        return cmd.get_result()

    def _from_path_settings(self):
        def get_settings():
            from django.conf import settings
            return settings

        settings = self._execute(get_settings)
        settings.configured = True
        return settings

    def lsapps(self):
        return self._settings.INSTALLED_OTREE_APPS

    def all_data(self):
        """Data for all apps in one DataFrame.

        There is one row per participant; different apps and rounds are stacked
        horizontally. This format is useful if you want to correlate
        participant's behavior in one app with their behavior in another app.

        """
        def _all_data():
            from otree import export
            rows = export.get_rows_for_wide_csv()
            return pd.DataFrame(rows)

        with mock.patch("django.conf.settings", self._settings):
            df = self._execute(_all_data)
        return df

    def time_expent(self):
        """Time spent on each page"""
        def _time_expent():
            from otree import export
            fp = io.StringIO()
            export.export_time_spent(fp)
            fp.seek(0)
            return pd.read_csv(fp)

        with mock.patch("django.conf.settings", self._settings):
            df = self._execute(_time_expent)
        return df

    def app(self, app_name):
        """Per-app data.

        These DataFrame contains a row for each player in the given app. If
        there are multiple rounds, there will be multiple rows for the same
        participant. This format is useful if you are mainly interested in
        one app, or if you want to correlate data between
        rounds of the same app.

        """
        if app_name not in self._settings.INSTALLED_OTREE_APPS:
            raise ValueError("Invalid app {}".format(app_name))

        def _app():
            from otree import export
            rows = export.get_rows_for_csv(app_name)
            return pd.DataFrame(rows)

        with mock.patch("django.conf.settings", self._settings):
            df = self._execute(_app)
        return df

    def doc(self, app_name):
        """Per-app documentation data."""
        if app_name not in self._settings.INSTALLED_OTREE_APPS:
            raise ValueError("Invalid app {}".format(app_name))

        def _doc():
            from otree import export
            fp = io.StringIO()
            export.export_docs(fp, app_name)
            return fp.getvalue()

        with mock.patch("django.conf.settings", self._settings):
            docs = self._execute(_doc)
        return docs

    @property
    def path(self):
        """Path of the oTree instance"""
        return self._path

    @property
    def settings(self):
        """setting of the oTree instance"""
        return self._settings
