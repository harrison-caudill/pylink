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
        code = m.best_modulation_code
        assert m.best_modulation_code.name == 'BPSK'

        # Make sure it's the middle
        m.override(e.allocation_hz, 1e6)
        m.override(e.cn0_db, 70)
        m.override(e.target_margin_db, 5)
        assert m.best_modulation_code.name == 'QPSK'

        # Make sure it's the highest
        m.override(e.allocation_hz, 1e3)
        m.override(e.cn0_db, 65)
        m.override(e.target_margin_db, 5)
        assert m.best_modulation_code.name == '8PSK'

        # Verify asymmetric spectral efficiencies work
        perf = [
            pylink.Code("Usable", 1, .5, 4),
            pylink.Code("Unusable", 1e-5, 1e5, 4),
            ]
        m.override(e.modulation_performance_table, perf)
        m.override(e.allocation_hz, 1e6)
        m.override(e.target_margin_db, 3)
        m.override(e.cn0_db, 60 + 7.02 + 5)

        code = m.best_modulation_code
        assert code.name == 'Usable'

    def test_modulation_code_obj(self, model):
        e = model.enum
        m = model

        perf = [pylink.Code("BPSK", .5, .5, 4)]
        m.override(e.modulation_performance_table, perf)
        code = m.best_modulation_code
        assert code

        # check the initial values
        assert code.name == 'BPSK'
        assert abs(code.esn0_db - 4.0) < 1e-5
        assert abs(code.tx_eff - .5) < 1e-5
        assert abs(code.rx_eff - .5) < 1e-5

        # check the ebn0
        assert abs(code.ebn0_db - 7.0102) < 1e-4

        # check another ebn0
        perf = [pylink.Code("8PSK", 2, 2, 12)]
        m.override(e.modulation_performance_table, perf)
        code = m.best_modulation_code
        assert abs(code.ebn0_db - 8.9898) < 1e-4

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
