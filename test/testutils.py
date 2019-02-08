#!/usr/bin/env python

import pylink
import pytest


@pytest.fixture
def example_rf_chain():
    return [
        pylink.Element(gain_db=-0.1,
                       noise_figure_db=0.1,
                       name='attenuator')
        ]


@pytest.fixture
def attenuator_1db():
    return pylink.Element(gain_db=-1,
                          noise_figure_db=1,
                          name='attenuator')

@pytest.fixture
def amplifier_10db():
    return pylink.Element(gain_db=10,
                          noise_figure_db=3,
                          name='amplifier')


perf = [
    pylink.Code("BPSK", .5, .5, 4),
    pylink.Code("QPSK", 1, 1, 8),
    pylink.Code("8PSK", 2, 2, 13),
    ]


@pytest.fixture
def model():
    return pylink.DAGModel([pylink.Geometry(),
                            pylink.Antenna(is_rx=True, tracking=True),
                            pylink.Interconnect(is_rx=True),
                            pylink.Receiver(),
                            pylink.Transmitter(),
                            pylink.Interconnect(is_rx=False),
                            pylink.Antenna(is_rx=False, tracking=False),
                            pylink.Channel(),
                            pylink.Modulation(name='QPSK', perf=perf),
                            pylink.LinkBudget()])
