#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
import inspect
import io

import numpy as np

import pandas as pd

import skotree


class SKoTreeTestCase(object):

    def __init__(self, path, has_session):
        self.path = path
        self.has_session = has_session
        self.methods = []
        self.is_remote = skotree.is_url(path)
        for mname in dir(self):
            method = getattr(self, mname)
            if mname.startswith("test_") and inspect.ismethod(method):
                self.methods.append(method)

    def setUp(self):
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
        assert apps == ["matching_pennies"]

    def test_lssessions(self):
        apps = self.otree.lssessions()
        assert apps == ["matching_pennies"]

    def test_session_config(self):
        self.otree.session_config("matching_pennies")
        try:
            self.otree.session_config("foo")
        except:
            pass
        else:
            raise AssertionError()

    def test_all_data(self):
        all_data = self.otree.all_data()
        must_be_empty = not self.has_session
        assert all_data.empty == must_be_empty
        assert all_data.columns.size == (49 if self.has_session else 0)

    def test_time_spent(self):
        tspent = self.otree.time_spent()
        assert tspent.empty == True
        assert len(tspent.columns) == 10

    def test_app_data_fail(self):
        try:
            self.otree.app_data("foo")
        except:
            pass
        else:
            raise AssertionError()

    def test_app_data(self):
        data = self.otree.app_data("matching_pennies")
        must_be_empty = not self.has_session
        assert data.empty == must_be_empty
        assert data.columns.size == 28

    def test_app_doc_fail(self):
        try:
            self.otree.app_doc("foo")
        except:
            pass
        else:
            raise AssertionError()

    def test_app_doc(self):
        doc = self.otree.app_doc("matching_pennies")
        assert isinstance(doc, str)

    def test_bot_data(self):
        store = self.otree.bot_data("matching_pennies", 2)
        assert isinstance(store.matching_pennies, pd.DataFrame)
        assert isinstance(store["matching_pennies"], pd.DataFrame)
        assert "matching_pennies" in store

        df = store.matching_pennies
        assert np.unique(df["participant.code"]).size == 2

        df = self.otree.bot_data("matching_pennies", 4).matching_pennies
        assert np.unique(df["participant.code"]).size == 4

    def test_bot_data_fail(self):
        try:
            self.otree.bot_data("matching_pennies", 3)
        except RuntimeError:
            pass
        else:
            raise AssertionError()

    def test_csv_store(self):
        store = skotree.CSVStore({"foo": io.StringIO()})
        assert "foo" in store
        assert "<CSVStore({foo})>" == repr(store)
        assert store.foo.empty


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", dest="path", required=True)

    sgroup = parser.add_mutually_exclusive_group(required=True)
    sgroup.add_argument("--session", dest="session", action="store_true")
    sgroup.add_argument("--no-session", dest="session", action="store_false")

    args = parser.parse_args()

    test_case = SKoTreeTestCase(args.path, args.session)
    test_case.run()
