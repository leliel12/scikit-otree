#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse

import skotree


class TestCase(object):

    def __init__(self, path, has_session):
        self.path = path
        self.has_session = has_session

    def run(self):
        otree = skotree.oTree(self.path)
#~ print(wissink.all_data())
#~ print(wissink.lsapps())
#~ print(wissink.time_expent())
#~ print(wissink.app("political_convention"))
#~ print(wissink.doc("political_convention"))

#~ print(wissink)
#~ print(wissink)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", dest="wrk_path", required=True)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--session", dest="session", action="store_true")
    group.add_argument("--no-session", dest="session", action="store_false")

    args = parser.parse_args()

    test_case = TestCase(args.wrk_path, args.session)
    test_case.run()
