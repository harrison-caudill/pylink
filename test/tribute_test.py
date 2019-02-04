#!/usr/bin/env python

import pylink
import pytest

from testutils import model


class TributeA(object):

    def __init__(self):
        self.tribute = {
            'a1': 1,
            'a2': 2,
            }


class TributeB(object):

    def __init__(self):
        self.tribute = {
            'b1': 1,
            'b2': 2,
            }

class TestTribute(object):

    def test_basic_tribute(self):
        a = TributeA()
        b = TributeB()
        m = pylink.DAGModel([a, b])

        assert 1 == m.a1
        assert 2 == m.a2
        assert 1 == m.b1
        assert 2 == m.b2
