#!/usr/bin/env python

import pylink
import pytest

from testutils import model


class TestChannel(object):

    def test_unity_gain_propagation_loss_db(self, model):
        e = model.enum
        m = model
        # eg values from pasternack's website
        m.override(e.slant_range_km, 100)
        m.override(e.center_freq_hz, 100e6)
        assert abs(m.unity_gain_propagation_loss_db - 112.4) < 5e-2

    def test_total_channel_loss_db(self, model):
        e = model.enum
        m = model
        m.override(e.unity_gain_propagation_loss_db, 1)
        m.override(e.atmospheric_loss_db, 1)
        m.override(e.ionospheric_loss_db, 1)
        m.override(e.rain_loss_db, 1)
        m.override(e.multipath_fading_db, 1)
        assert abs(m.total_channel_loss_db - 5) < 1e-6

    def test_wavelength_m(self, model):
        e = model.enum
        m = model
        l = 2.99792458
        m.override(e.center_freq_hz, 100e6)
        assert abs(m.wavelength_m - l) < 1e-4

    def test_bitrate_dbhz(self, model):
        e = model.enum
        m = model
        m.override(e.bitrate_hz, 1e5)
        assert abs(m.bitrate_dbhz - 50) < 1e-6

    def test_allocation_start_hz(self, model):
        e = model.enum
        m = model

        m.override(e.center_freq_hz, 400e6)
        m.override(e.allocation_hz, 1e6)
        assert abs(m.allocation_start_hz - 399.5e6) < 1e-4

    def test_allocation_end_hz(self, model):
        e = model.enum
        m = model

        m.override(e.center_freq_hz, 400e6)
        m.override(e.allocation_hz, 1e6)
        assert abs(m.allocation_end_hz - 400.5e6) < 1e-4

    def test_required_tx_bw_hz(self, model):
        e = model.enum
        m = model

        m.tx_spectral_efficiency_bps_per_hz = 2
        m.override(e.bitrate_hz, 50e3)

        assert abs(m.required_tx_bw_hz - 25e3) < 1e-4

    def test_required_rx_bw_hz(self, model):
        e = model.enum
        m = model

        m.rx_spectral_efficiency_bps_per_hz = 2
        m.override(e.bitrate_hz, 50e3)

        assert abs(m.required_rx_bw_hz - 25e3) < 1e-4

    def test_required_tx_bw_dbhz(self, model):
        e = model.enum
        m = model

        m.tx_spectral_efficiency_bps_per_hz = 1
        m.override(e.required_tx_bw_hz, 1e3)

        assert abs(m.required_tx_bw_dbhz - 30) < 1e-4

    def test_required_rx_bw_dbhz(self, model):
        e = model.enum
        m = model

        m.rx_spectral_efficiency_bps_per_hz = 1
        m.override(e.required_rx_bw_hz, 1e3)

        assert abs(m.required_rx_bw_dbhz - 30) < 1e-4
