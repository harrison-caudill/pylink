#!/usr/bin/python

import pylink
import pytest

from testutils import model


class TestBudget(object):

    def test_rx_power_dbw(self, model):
        e = model.enum
        m = model
        m.override(e.tx_eirp_dbw, 20)
        m.override(e.total_channel_loss_db, 100)
        m.override(e.polarization_mismatch_loss_db, 3)
        assert abs(m.rx_power_dbw - -83.0) < 1e-6

    def test_pf_dbw_per_m2(self, model):
        e = model.enum
        m = model
        m.override(e.tx_eirp_dbw, 21.5)
        m.override(e.slant_range_km, 2045)
        m.override(e.atmospheric_loss_db, .5)
        m.override(e.ionospheric_loss_db, .5)
        m.override(e.rain_loss_db, 0)
        m.override(e.multipath_fading_db, 0)
        assert abs(m.pf_dbw_per_m2 - -116.71) < 1e-2

    def test_rx_antenna_effective_area_dbm2(self, model):
        e = model.enum
        m = model
        m.override(e.rx_antenna_gain_dbi, -6)
        m.override(e.wavelength_m, 0.745)
        assert abs(m.rx_antenna_effective_area_dbm2 - -19.55) < 1e-2

    def test_rx_g_over_t_db(self, model):
        e = model.enum
        m = model
        m.override(e.rx_antenna_gain_dbi, -6)
        m.override(e.rx_noise_temp_k, 2786)
        assert abs(m.rx_g_over_t_db - -40.45) < 1e-3

    def test_rx_n0_dbw_per_hz(self, model):
        e = model.enum
        m = model
        m.override(e.rx_noise_temp_k, 2786)
        assert abs(m.rx_n0_dbw_per_hz - -194.15) < 1e-3

    def test_cn0_db(self, model):
        e = model.enum
        m = model
        m.override(e.rx_power_dbw, -130)
        m.override(e.rx_n0_dbw_per_hz, -100)
        assert abs(m.cn0_db - -30) < 1e-6

    def test_mismatched_bandwidth_loss_db(self, model):
        e = model.enum
        m = model
        m.override(e.rx_noise_bw_hz, 1e6)
        m.override(e.required_bw_hz, 1e5)
        assert abs(m.excess_noise_bandwidth_loss_db - 10) < 1e-6

    def test_rx_eb(self, model):
        e = model.enum
        m = model
        m.override(e.rx_power_dbw, -60)
        m.override(e.bitrate_dbhz, 40)
        assert abs(m.rx_eb - -100) < 1e-6

    def test_rx_ebn0_db(self, model):
        e = model.enum
        m = model
        m.override(e.rx_eb, 10)
        m.override(e.rx_n0_dbw_per_hz, 40)
        assert abs(m.rx_ebn0_db - -30) < 1e-4

    def test_link_margin_db(self, model):
        e = model.enum
        m = model
        req_ebn0 = m.required_ebn0_db
        m.override(e.rx_ebn0_db, 50)
        m.override(e.excess_noise_bandwidth_loss_db, 10)
        assert abs(m.link_margin_db - (40 - req_ebn0)) < 1e-4

    def test_pfd_dbw_per_m2_per_4khz(self, model):
        e = model.enum
        m = model
        m.override(e.pf_dbw_per_m2, -100)
        m.override(e.bitrate_hz,
                   m.tx_spectral_efficiency_bps_per_hz * 40e3)
        assert abs(m.pfd_dbw_per_m2_per_4khz - -110) < 1e-6

    def test_tx_inline_losses_db(self, model):
        e = model.enum
        m = model

        radio_chain = [pylink.Element(name='x', gain_db=-1, noise_figure_db=1)]
        inter_chain = [pylink.Element(name='x', gain_db=-1, noise_figure_db=1)]
        ant_chain = [pylink.Element(name='x', gain_db=-1, noise_figure_db=1)]

        m.override(e.transmitter_rf_chain, radio_chain)
        m.override(e.tx_interconnect_rf_chain, inter_chain)
        m.override(e.tx_antenna_rf_chain, ant_chain)

        assert abs(m.tx_inline_losses_db - 3) < 1e-5

    def test_tx_power_at_antenna_dbw(self, model):
        e = model.enum
        m = model

        m.override(e.tx_inline_losses_db, 5.7)
        m.override(e.tx_power_at_pa_dbw, 5.7)

        assert abs(m.tx_power_at_antenna_dbw) < 1e-5

    def test_rx_rf_chain(self, model):
        e = model.enum
        m = model

        radio_chain = [pylink.Element(name='a', gain_db=-1, noise_figure_db=1)]
        inter_chain = [pylink.Element(name='b', gain_db=-2, noise_figure_db=2)]
        ant_chain = [pylink.Element(name='c', gain_db=-3, noise_figure_db=3)]

        m.override(e.receiver_rf_chain, radio_chain)
        m.override(e.rx_interconnect_rf_chain, inter_chain)
        m.override(e.rx_antenna_rf_chain, ant_chain)

        chain = ant_chain + inter_chain + radio_chain
        assert m.rx_rf_chain == chain
