#!/usr/bin/env python

import math
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

    def test_human_hz(self):
        for v, s in {1.0:    (1.0,   'Hz'),
                     1.1e1:  (11.0,  'Hz'),
                     1.1e2:  (110.0, 'Hz'),
                     1.1e3:  (1.1,   'kHz'),
                     1.1e4:  (11.0,  'kHz'),
                     1.1e5:  (110.0, 'kHz'),
                     1.1e6:  (1.1,   'MHz'),
                     1.1e7:  (11.0,  'MHz'),
                     1.1e8:  (110.0, 'MHz'),
                     1.1e9:  (1.1,   'GHz'),
                     1.1e10: (11.0,  'GHz'),
                     1.1e11: (110.0, 'GHz')}.iteritems():
            good = s
            questionable = pylink.human_hz(v)
            assert abs(good[0] - questionable[0]) < 1e-6
            assert good[1] == questionable[1]

    def test_human_m(self):
        for v, s in {1.1e-4: (0.11,  'mm'),
                     1.1e-3: (1.1,   'mm'),
                     1.1e-2: (1.1,   'cm'),
                     1.1e-1: (11.0,  'cm'),
                     1.1e0:  (1.1,   'm'),
                     1.1e1:  (11.0,  'm'),
                     1.1e2:  (110.0, 'm'),
                     1.1e3:  (1.1,   'km'),
                     1.1e4:  (11.0,  'km'),}.iteritems():
            good = s
            questionable = pylink.human_m(v)
            assert abs(good[0] - questionable[0]) < 1e-6
            assert good[1] == questionable[1]

    def test_spreading_loss_db(self):
        assert abs(pylink.spreading_loss_db(0.5e-3)
                   - pylink.to_db(math.pi)) < 1e-3
