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
        with cd(self._path), mock.patch("sys.argv", ["", "check"]):
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
    """Connection to an oTree deployment.

    This class are in charge to retrieve the data from some oTree database
    without change the local environment

    Parameters
    ----------
    path : string
        The path where the settings.py of the deployment are located

    """

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
        """List all available oTree apps instaleed in the deployment.

        Returns
        -------

        list:
            list with the installed oTree apps

        """
        return self._settings.INSTALLED_OTREE_APPS

    def all_data(self):
        """Data for all apps in one DataFrame.

        There is one row per participant; different apps and rounds are stacked
        horizontally. This format is useful if you want to correlate
        participant's behavior in one app with their behavior in another app.

        Returns
        -------

        data: :py:class:`pandas.DataFrame`
            DataFrame with one row per participant.

        """
        def _all_data():
            from otree import export
            fp = io.StringIO()
            export.export_wide(fp, file_extension='csv')
            fp.seek(0)
            return fp

        fp = self._execute(_all_data)
        try:
            return pd.read_csv(fp)
        except pd.errors.EmptyDataError:
            return pd.DataFrame()

    def time_expent(self):
        """Time spent on each page

        Returns
        -------

        data: :py:class:`pandas.DataFrame`
            DataFrame with one row per participant per session.

        """
        def _time_expent():
            from otree import export
            fp = io.StringIO()
            export.export_time_spent(fp)
            fp.seek(0)
            return fp

        fp = self._execute(_time_expent)
        try:
            return pd.read_csv(fp)
        except pd.errors.EmptyDataError:
            return pd.DataFrame()

    def app_data(self, app_name):
        """Per-app data.

        These DataFrame contains a row for each player in the given app. If
        there are multiple rounds, there will be multiple rows for the same
        participant. This format is useful if you are mainly interested in
        one app, or if you want to correlate data between
        rounds of the same app.

        Parameters
        ----------

        app_name : string
            name of the oTree app to retrieve the documentation.
            (Check ``oTree.lsapps())`` for the avaulable names)

        Returns
        -------

        data: :py:class:`pandas.DataFrame`
            DataFrame with one row for each player in the given app.


        """
        if app_name not in self._settings.INSTALLED_OTREE_APPS:
            raise ValueError("Invalid app {}".format(app_name))

        def _app():
            from otree import export
            fp = io.StringIO()
            export.export_app(app_name, fp, file_extension='csv')
            fp.seek(0)
            return fp

        fp = self._execute(_app)
        try:
            return pd.read_csv(fp)
        except pd.errors.EmptyDataError:
            return pd.DataFrame()

    def app_doc(self, app_name):
        """Per-app documentation data.

        Parameters
        ----------

        app_name : string
            name of the oTree app to retrieve the documentation.
            (Check ``oTree.lsapps())`` for the avaulable names)

        Returns
        -------

        docs: :py:class:`str`
            String with the description of the data of the given app.

        """
        if app_name not in self._settings.INSTALLED_OTREE_APPS:
            raise ValueError("Invalid app {}".format(app_name))

        def _doc():
            from otree import export
            fp = io.StringIO()
            export.export_docs(fp, app_name)
            fp.seek(0)
            return fp

        fp = self._execute(_doc)
        return fp.getvalue()

    @property
    def path(self):
        """Path of the oTree instance"""
        return self._path

    @property
    def settings(self):
        """setting of the oTree instance"""
        return self._settings
