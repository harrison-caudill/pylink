#!/usr/bin/python

import pylink
import pytest

class TestUtils(object):

    def test_to_db(self):
        assert abs(pylink.to_db(10) - 10) < 1e-6
        assert abs(pylink.to_db(2) - 3) < 0.1

    def test_from_db(self):
        assert abs(pylink.from_db(10) - 10) < 1e-6
        assert abs(pylink.from_db(3) - 2) < 0.1

    def test_e_field_to_eirp_dbw(self):
        # http://www.ti.com/lit/an/swra048/swra048.pdf
        eirp_dbw = pylink.e_field_to_eirp_dbw(200e-6, 3)
        assert abs(eirp_dbw+30 - -49.2) < 1e-2

    def test_dbw_to_e_field_v_per_m(self):
        E = pylink.eirp_dbw_to_e_field_v_per_m(-49.2-30, 3)
        assert abs(E - 200e-6) < 1e-2

