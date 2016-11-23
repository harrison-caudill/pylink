#!/usr/bin/python

import pylink
import pytest

from testutils import model


class TestModulation(object):
    """These all assume the modulation found in the fixture.
    """

    def test_best_modulation_code(self, model):
        e = model.enum
        m = model

        # Make sure it's the lowest
        m.override(e.allocation_hz, 1e9)
        m.override(e.cn0_db, 65)
        m.override(e.target_margin_db, 5)
        assert m.best_modulation_code.name == 'BPSK'

        # Make sure it's the middle
        m.override(e.allocation_hz, 1e6)
        m.override(e.cn0_db, 73)
        m.override(e.target_margin_db, 5)
        assert m.best_modulation_code.name == 'QPSK'

        # Make sure it's the highest
        m.override(e.allocation_hz, 1e3)
        m.override(e.cn0_db, 65)
        m.override(e.target_margin_db, 5)
        assert m.best_modulation_code.name == '8PSK'

    def test_tx_spectral_efficiency_bps_per_hz(self, model):
        e = model.enum
        m = model

        m.override(e.allocation_hz, 1e6)
        m.override(e.cn0_db, 73)
        m.override(e.target_margin_db, 5)
        assert m.tx_spectral_efficiency_bps_per_hz == 1

    def test_rx_spectral_efficiency_bps_per_hz(self, model):
        e = model.enum
        m = model

        m.override(e.allocation_hz, 1e6)
        m.override(e.cn0_db, 73)
        m.override(e.target_margin_db, 5)
        assert m.rx_spectral_efficiency_bps_per_hz == 1

    def test_required_demod_ebn0_db(self, model):
        e = model.enum
        m = model
        
        m.override(e.allocation_hz, 1e6)
        m.override(e.cn0_db, 73)
        m.override(e.target_margin_db, 5)
        assert m.required_demod_ebn0_db == 8
