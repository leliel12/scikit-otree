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

__version__ = ("0", "3")

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
import logging
import io
import pickle
import multiprocessing as mp
from collections import Mapping
from unittest import mock

if os.getenv("SKOTREE_IN_SETUP") != "True":
    import pandas as pd

# =============================================================================
# CONSTANS AND LOGGERS
# =============================================================================

logger = logging.getLogger("skotree")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


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


class CSVStore(Mapping):

    def __init__(self, d):
        self._d = dict(d)

    def __repr__(self):
        keys = "{" + ", ".join(self._d.keys()) + "}"
        return "<CSVStore({})>".format(keys)

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def __dir__(self):
        return list(self.keys())

    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError:
            raise AttributeError(k)

    def __getitem__(self, k):
        fp = self._d[k]
        try:
            return pd.read_csv(fp)
        except pd.errors.EmptyDataError:
            return pd.DataFrame()
        finally:
            fp.seek(0)


class oTreeContextProcess(mp.Process):

    def __init__(self, path, func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._path = path
        self._func = func
        self._queue = mp.Queue()

    def __repr__(self):
        return "oTree@{}$ {}".format(self._path, self._func)

    def run(self):
        try:
            with cd(self._path), mock.patch("sys.argv", ["", "check"]):
                with mock.patch("sys.stdout"), mock.patch("warnings.warn"):
                    from otree.management import cli
                    cli.otree_cli()
                result = self._func()
        except Exception as err:
            result = err
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
        logger.debug("Starting remote oTree process...")
        cmd.start()
        logger.debug("Wating for the result...")
        cmd.join()
        logger.debug("Retrieving result")
        result = cmd.get_result()
        if isinstance(result, BaseException):
            logger.debug("Remote procees raises an exception!")
            raise result
        return result

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

    def lssessions(self):
        """List all available oTree session configured in the deployment.

        Returns
        -------

        list:
            list with the installed oTree sessions

        """
        return [s["name"] for s in self._settings.SESSION_CONFIGS]

    def session_config(self, session_name):
        """Retrieve the configuration of the given session.

        Returns
        -------

        dict:
            dict with the default and specific configuration for a session

        """
        config = dict(self._settings.SESSION_CONFIG_DEFAULTS)
        for s in self._settings.SESSION_CONFIGS:
            if s["name"] == session_name:
                config.update(s)
                return config
        raise ValueError("Invalid session_name {}".format(session_name))

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
            (Check ``oTree.lsapps())`` for the available names)

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
            (Check ``oTree.lsapps())`` for the available names)

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

    def bot_data(self, session_name, num_participants=None):
        """Discover and run the experiment tests and retrieve the data
        generated by them.

        Parameters
        ----------

        session_name : string
            name of the session configured in oTree.
            (Check ``oTree.lssession())`` for the available names)
        num_participants : int or None
            Number of participants, defaults to minimum for the session config
            (check ``oTree.session_config(session_name)``).

        Returns
        -------

        CSVStore :
            Mapped type wiht one key per app inside app_sequence of the
            session.

        """
        config = self.session_config(session_name)
        num_participants = (
            config["num_demo_participants"]
            if num_participants is None
            else num_participants)

        def _bot_data():
            # based on bots otree command
            from django.conf import settings, global_settings
            from otree import common_internal
            from otree.bots.runner import run_pytests

            common_internal.USE_REDIS = False

            settings.STATICFILES_STORAGE = global_settings.STATICFILES_STORAGE
            settings.CHANNEL_LAYERS['default'] = (
                settings.INMEMORY_CHANNEL_LAYER)
            settings.WHITENOISE_AUTOREFRESH = True

            bots_logger = logging.getLogger('otree.bots')
            bots_logger.setLevel(logging.WARNING)

            # mock for not create dirs and also store the data into StringIO
            fps = {aname: io.StringIO() for aname in config["app_sequence"]}

            @contextlib.contextmanager
            def export_app_wrap(fpath, *args, **kwargs):
                basename = os.path.basename(fpath)
                aname = os.path.splitext(basename)[0]
                fp = fps[aname]
                yield fp
                fp.seek(0)

            logger.info("Running bots, pleae wait...")

            stdout = io.StringIO()
            with mock.patch("os.makedirs"), mock.patch("sys.stdout", stdout), \
                 mock.patch("os.path.isdir", return_value=False), \
                 mock.patch("codecs.open", export_app_wrap):
                    exit_code = run_pytests(
                        session_config_name=session_name,
                        num_participants=num_participants,
                        preserve_data=True,
                        export_path="virtual_skotree",
                        verbosity=-1)

            if exit_code:
                raise RuntimeError(stdout.getvalue())

            return fps

        fps = self._execute(_bot_data)
        store = CSVStore(fps)
        return store

    @property
    def path(self):
        """Path of the oTree instance"""
        return self._path

    @property
    def settings(self):
        """setting of the oTree instance"""
        return self._settings
