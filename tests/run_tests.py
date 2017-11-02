#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import inspect
import io
import unittest
import atexit
import time
import urllib.parse as urlparse

import sh

import requests

import numpy as np

import pandas as pd

import skotree


class SKoTreeTestCase(object):

    def __init__(self, path, has_session):
        self.path = path
        self.has_session = has_session
        self.methods = []
        self.is_remote = skotree.is_url(path)
        self.proc = None
        self.check = unittest.TestCase('__init__')
        for mname in dir(self):
            method = getattr(self, mname)
            if mname.startswith("test_") and inspect.ismethod(method):
                self.methods.append(method)

    def __getattr__(self, n):
        return getattr(self.check, n)

    def setUp(self):
        if self.is_remote and self.proc is None:
            netloc = urlparse.urlparse(self.path).netloc
            self.proc = sh.otree.runserver(netloc, _bg=True)

            def kill_proc():
                self.proc.process.terminate()

            atexit.register(kill_proc)

            while True:
                try:
                    requests.get(self.path)
                except requests.ConnectionError:
                    time.sleep(2)
                else:
                    break

        if self.is_remote:
            self.otree = skotree.oTree(
                self.path, username="admin", password="skotree")
        else:
            self.otree = skotree.oTree(self.path)

    def tearDown(self):
        del self.otree

    def run(self):
        for method in self.methods:
            print("[RUNNING] {}.{}".format(
                type(self).__name__, method.__name__))
            self.setUp()
            try:
                method()
            finally:
                self.tearDown()

    def test_lsapps(self):
        apps = self.otree.lsapps()
        if self.is_remote and not self.has_session:
            self.assertIsNone(apps)
        else:
            self.assertEquals(apps, ["matching_pennies"])

    def test_lssessions(self):
        apps = self.otree.lssessions()
        self.assertEquals(apps, ["matching_pennies"])

    def test_session_config(self):
        if self.is_remote:
            with self.assertRaises(NotImplementedError):
                self.otree.session_config("matching_pennies")
        else:
            self.otree.session_config("matching_pennies")
            with self.assertRaises(Exception):
                self.otree.session_config("foo")

    def test_all_data(self):
        all_data = self.otree.all_data()
        must_be_empty = not self.has_session
        self.assertEquals(all_data.empty, must_be_empty)
        self.assertEquals(
            all_data.columns.size, (49 if self.has_session else 0))

    def test_time_spent(self):
        tspent = self.otree.time_spent()
        self.assertTrue(tspent.empty)
        self.assertEquals(len(tspent.columns), 10)

    def test_app_data_fail(self):
        with self.assertRaises(Exception):
            self.otree.app_data("foo")

    def test_app_data(self):
        data = self.otree.app_data("matching_pennies")
        must_be_empty = not self.has_session
        self.assertEquals(data.empty, must_be_empty)
        self.assertEquals(data.columns.size, 28)

    def test_app_doc_fail(self):
        with self.assertRaises(Exception):
            self.otree.app_doc("foo")

    def test_app_doc(self):
        doc = self.otree.app_doc("matching_pennies")
        self.assertIsInstance(doc, str)

    def test_bot_data(self):
        if self.is_remote:
            with self.assertRaises(NotImplementedError):
                self.otree.bot_data("matching_pennies", 2)
        else:
            store = self.otree.bot_data("matching_pennies", 2)
            self.assertIsInstance(store.matching_pennies, pd.DataFrame)
            self.assertIsInstance(store["matching_pennies"], pd.DataFrame)
            self.assertIn("matching_pennies", store)

            df = store.matching_pennies
            self.assertEquals(np.unique(df["participant.code"]).size, 2)

            df = self.otree.bot_data("matching_pennies", 4).matching_pennies
            self.assertEquals(np.unique(df["participant.code"]).size, 4)

    def test_bot_data_fail(self):
        if self.is_remote:
            with self.assertRaises(NotImplementedError):
                self.otree.bot_data("matching_pennies", 3)
        else:
            with self.assertRaises(Exception):
                self.otree.bot_data("matching_pennies", 3)

    def test_csv_store(self):
        store = skotree.CSVStore({"foo": io.StringIO()})
        self.assertIn("foo", store)
        self.assertEquals("<CSVStore({foo})>", repr(store))
        self.assertTrue(store.foo.empty)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", dest="path", required=True)

    sgroup = parser.add_mutually_exclusive_group(required=True)
    sgroup.add_argument("--session", dest="session", action="store_true")
    sgroup.add_argument("--no-session", dest="session", action="store_false")

    args = parser.parse_args()

    test_case = SKoTreeTestCase(args.path, args.session)
    test_case.run()
