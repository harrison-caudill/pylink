#!/usr/bin/env python

import pylink
import pytest

from testutils import model


class TestTransmitter(object):

    def test_tx_eirp_dbw(self, model):
        e = model.enum
        m = model
        m.override(e.tx_power_at_antenna_dbw, 10)
        m.override(e.tx_antenna_gain_dbi, 10)
        assert abs(m.tx_eirp_dbw - 20) < 1e-6

    def test_peak_tx_eirp_dbw(self, model):
        e = model.enum
        m = model
        m.override(e.tx_power_at_antenna_dbw, 10)
        m.override(e.tx_antenna_gain_dbi, 10)
        m.override(e.tx_antenna_peak_gain_dbi, 20)
        assert abs(m.tx_eirp_dbw - 20) < 1e-6
        assert abs(m.peak_tx_eirp_dbw - 30) < 1e-6

    def test_tx_power_at_antenna_dbw(self, model):
        e = model.enum
        m = model
        m.override(e.tx_power_at_pa_dbw, 10)
        m.override(e.tx_inline_losses_db, 3)
        assert abs(m.tx_power_at_antenna_dbw - 7) < 1e-6
