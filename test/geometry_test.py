#!/usr/bin/python

import pylink
import pytest

from testutils import model


class TestOrbit(object):

    def test_mean_orbit_altitude_km(self, model):
        e = model.enum
        m = model
        m.override(e.apoapsis_altitude_km, 100)
        m.override(e.periapsis_altitude_km, 300)

        # this one is pretty straight-forward
        assert abs(m.mean_orbit_altitude_km - 200) < 1e-6

    def test_slant_range_km(self, model):
        e = model.enum
        m = model
        m.override(e.apoapsis_altitude_km, 600)
        m.override(e.periapsis_altitude_km, 600)
        m.override(e.min_elevation_deg, 10)

        # http://www.rfwireless-world.com/calculators/satellite-slant-range-calculator.html
        assert abs(m.slant_range_km - 1932.2446843632927) < 0.1

    def test_satellite_antenna_angle_deg(self, model):
        e = model.enum
        m = model
        m.override(e.apoapsis_altitude_km, 600)
        m.override(e.periapsis_altitude_km, 600)
        m.override(e.min_elevation_deg, 10)

        # http://www.rfwireless-world.com/calculators/satellite-slant-range-calculator.html
        assert abs(m.satellite_antenna_angle_deg - 64.1750983843174) < 1e-3

    def test_rx_polarization_loss_db(self):
        # FIXME(kungfoo): implement
        pass


    def test_geo_altitude_km(self, model):
        e = model.enum
        m = model

        assert abs(m.geo_altitude_km - 35786) < 1


    def test_tx_distance_to_geo_km(self, model):
        e = model.enum
        m = model

        m.override(e.apoapsis_altitude_km, 100)
        m.override(e.periapsis_altitude_km, 300)
        assert abs(m.tx_distance_to_geo_km - (35786 - 100)) < 1

        m.override(e.apoapsis_altitude_km, 100)
        m.override(e.periapsis_altitude_km, 100)
        assert abs(m.tx_distance_to_geo_km - (35786 - 100)) < 1

    def test_periapsis_slant_range_km(self, model):
        e = model.enum
        m = model

        m.override(e.apoapsis_altitude_km, 600)
        m.override(e.periapsis_altitude_km, 600)
        m.override(e.min_elevation_deg, 10)

        # http://www.rfwireless-world.com/calculators/satellite-slant-range-calculator.html
        assert abs(m.periapsis_slant_range_km - 1932.2446843632927) < 0.1

        m.override(e.apoapsis_altitude_km, 1000)
        m.override(e.periapsis_altitude_km, 600)
        m.override(e.min_elevation_deg, 10)

        # http://www.rfwireless-world.com/calculators/satellite-slant-range-calculator.html
        assert abs(m.periapsis_slant_range_km - 1932.2446843632927) < 0.1
