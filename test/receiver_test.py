#!/usr/bin/env python

import pylink
import pytest

from testutils import model, attenuator_1db, amplifier_10db

class TestReceiver(object):

    def test_rx_noise_temp_k(self, model):
        e = model.enum
        m = model
        m.override(e.rx_system_noise_temp_k, 100)
        m.override(e.rx_antenna_noise_temp_k, 100)

        # verifies that the rx noise temperature is antenna + rx system
        assert abs(m.rx_noise_temp_k - 200) < 1e-4

    def test_rx_system_noise_temp_k(self,
                                    model,
                                    attenuator_1db,
                                    amplifier_10db):
        e = model.enum
        m = model

        # https://www.ieee.li/pdf/viewgraphs_mohr_noise.pdf

        # FIXME: We need some black-box tests for this one
        att_temp = 75.08836942
        amp_temp = 363.3586957

        m.override(e.rx_rf_chain, [attenuator_1db])
        assert abs(m.rx_system_noise_temp_k - att_temp) < 1e-3

        m.override(e.rx_rf_chain, [attenuator_1db, amplifier_10db])
        assert abs(m.rx_system_noise_temp_k - att_temp - amp_temp) < 1e-3

    def test_rx_noise_temp_dbk(self, model):
        e = model.enum
        m = model
        m.override(e.rx_noise_temp_k, 1e3)
        assert abs(m.rx_noise_temp_dbk - 30) < 1e-6

    def test_rx_system_noise_factor(self,
                                    model,
                                    attenuator_1db,
                                    amplifier_10db):
        e = model.enum
        m = model

        att_temp = 75.08836942
        att_fact = 1.258925412
        amp_temp = 363.3586957
        amp_fact = 1.25296102

        m.override(e.rx_rf_chain, [attenuator_1db, amplifier_10db])
        assert abs(m.rx_system_noise_factor - att_fact - amp_fact) < 1e-3

    def test_rx_system_noise_figure(self, model):
        e = model.enum
        m = model
        m.override(e.rx_system_noise_factor, 1e2)
        assert abs(m.rx_system_noise_figure - 20) < 1e-6
