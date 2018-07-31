#!/usr/bin/python

import pylink
import pytest

from testutils import model

class TestAntenna(object):

    def test_gain_dbi(self, model):
        e = model.enum
        m = model

        pattern = range(10)
        antenna = pylink.Antenna(
            is_rx=False,
            tracking=False,
            pattern=pattern)
        m.accept_tribute(antenna.tribute)
        model.clear_cache()

        assert 360 == len(m.tx_antenna_gain_pattern_angles)

        for i in range(-180, 180, 1):
            m.override(e.tx_antenna_angle_deg, i)
            gain = m.tx_antenna_gain_dbi
            deg = (360+i) % 360
            val = antenna.interpolated[deg]
            assert gain == val

        for i in range(360):
            m.override(e.tx_antenna_angle_deg, i)
            gain = m.tx_antenna_gain_dbi
            val = antenna.interpolated[i]
            assert gain == val

    def test_peak_gain_dbi(self, model):
        e = model.enum
        m = model
        pattern = range(10)
        antenna = pylink.Antenna(
            is_rx=False,
            tracking=False,
            pattern=pattern)
        m.accept_tribute(antenna.tribute)
        model.clear_cache()

        assert max(antenna.interpolated) == m.tx_antenna_peak_gain_dbi


    def test_angle_deg(self, model):
        # any test of this would just be duplication of the same code
        pass

    def test_boresight_gain_dbi(self, model):
        assert model.tx_antenna_boresight_gain_dbi == 0
        pattern = range(1, 10, 1)
        antenna = pylink.Antenna(
            is_rx=False,
            tracking=False,
            pattern=pattern)
        model.accept_tribute(antenna.tribute)
        model.clear_cache()
        assert model.tx_antenna_boresight_gain_dbi == 1

    def test_average_gain_dbi(self, model):
        e = model.enum
        m = model
        pattern = range(10)
        antenna = pylink.Antenna(
            is_rx=False,
            tracking=False,
            pattern=pattern)
        m.accept_tribute(antenna.tribute)
        model.clear_cache()

        assert m.tx_antenna_average_gain_dbi == sum(antenna.interpolated)/360.0

    def test_average_nadir_gain_dbi(self, model):
        e = model.enum
        m = model
        pattern = [1]*90 + [0]*180 + [1]*90
        antenna = pylink.Antenna(
            is_rx=False,
            tracking=False,
            pattern=pattern)
        m.accept_tribute(antenna.tribute)
        model.clear_cache()

        assert(1 == m.tx_antenna_average_nadir_gain_dbi)

    def test_polarization(self, model):
        assert 'rhcp'.upper() == model.tx_antenna_polarization

    def test_raw_gain_pattern(self, model):
        e = model.enum
        m = model
        pattern = range(10)
        antenna = pylink.Antenna(
            is_rx=False,
            tracking=False,
            pattern=pattern)
        m.accept_tribute(antenna.tribute)
        model.clear_cache()

        for i in range(len(pattern)):
            assert m.tx_antenna_raw_gain_pattern[i] == pattern[i]

    def test_raw_gain_pattern_angles(self, model):
        e = model.enum
        m = model
        pattern = range(36)
        antenna = pylink.Antenna(
            is_rx=False,
            tracking=False,
            pattern=pattern)
        m.accept_tribute(antenna.tribute)
        model.clear_cache()

        for i in range(len(m.tx_antenna_raw_gain_pattern_angles)):
            assert m.tx_antenna_raw_gain_pattern_angles[i] == 10*i

        pattern = range(7)
        antenna = pylink.Antenna(
            is_rx=False,
            tracking=False,
            pattern=pattern)
        m.accept_tribute(antenna.tribute)
        model.clear_cache()

        angles = m.tx_antenna_raw_gain_pattern_angles
        for i in range(len(angles)):
            assert angles[i] == i*(360.0/len(pattern))

    def test_gain_pattern(self, model):
        e = model.enum
        m = model
        pattern = [1]*3 + [0]*5 + [1]*2
        antenna = pylink.Antenna(
            is_rx=False,
            tracking=False,
            pattern=pattern)
        m.accept_tribute(antenna.tribute)
        model.clear_cache()

        interp = m.tx_antenna_gain_pattern
        assert 360 == len(interp)

        for i in range(-30, 30, 1):
            angle = (360 + i) % 360
            assert abs(interp[angle] - 1.0) < 3e-2

    def test_gain_pattern_angles(self, model):
        e = model.enum
        m = model
        pattern = range(7)
        antenna = pylink.Antenna(
            is_rx=False,
            tracking=False,
            pattern=pattern)
        m.accept_tribute(antenna.tribute)
        model.clear_cache()

        angles = m.tx_antenna_gain_pattern_angles
        assert 360 == len(angles)
        for i in range(len(angles)):
            assert i == angles[i]

    def test_obj(self, model):
        e = model.enum
        m = model
        pattern = range(7)
        antenna = pylink.Antenna(
            is_rx=False,
            tracking=False,
            pattern=pattern)
        m.accept_tribute(antenna.tribute)
        model.clear_cache()
        assert m.tx_antenna_obj == antenna

    def test_tracking_target(self, model):
        e = model.enum
        m = model
        pattern = range(7)
        antenna = pylink.Antenna(
            is_rx=False,
            tracking=False,
            pattern=pattern)
        m.accept_tribute(antenna.tribute)
        model.clear_cache()

        assert not m.tx_antenna_tracking_target

        e = model.enum
        m = model
        pattern = range(7)
        antenna = pylink.Antenna(
            is_rx=False,
            tracking=True,
            pattern=pattern)
        m.accept_tribute(antenna.tribute)
        model.clear_cache()

        assert True == m.tx_antenna_tracking_target

        e = model.enum
        m = model
        pattern = range(7)
        antenna = pylink.Antenna(
            is_rx=False,
            tracking='turkey saussage',
            pattern=pattern)
        m.accept_tribute(antenna.tribute)
        model.clear_cache()

        assert m.tx_antenna_tracking_target
        assert True == m.tx_antenna_tracking_target


    def test_rf_chain(self, model):
        e = model.enum
        m = model
        chain = range(3)
        pattern = range(7)
        antenna = pylink.Antenna(
            rf_chain=chain,
            is_rx=False,
            tracking=False,
            pattern=pattern)
        m.accept_tribute(antenna.tribute)
        model.clear_cache()

        assert m.tx_antenna_rf_chain == chain

    def test_pointing_loss_db(self, model):
        e = model.enum
        m = model
        pattern = range(7)
        antenna = pylink.Antenna(
            pointing_loss_db=2.718281828,
            is_rx=False,
            tracking=False,
            pattern=pattern)
        m.accept_tribute(antenna.tribute)
        model.clear_cache()

        assert m.tx_antenna_pointing_loss_db == 2.718281828
