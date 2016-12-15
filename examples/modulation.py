#!/usr/bin/python

import os

import pylink
from eg_budgets import DOWNLINK

"""Example of using a complex modulation with many code options.

Complex modulations, such as DVB-S2(X) have many different code-rate
options available for variable/adaptive bitrates, or encoder/decoder
capabilities, etc.  The ability to specify multiple code options and
select the appropriate option for the circumstances (largely dependent
upon the allocation size and the received C/N0) is included.
"""

m = DOWNLINK
e = m.enum

# Modify our boilerplate model to illustrate the coding
m.override(e.allocation_hz, 5e6)
m.override(e.cn0_db, 73)
m.override(e.target_margin_db, 1)
m.override(e.implementation_loss_db, 1)

# Observe the best code option
code = m.best_modulation_code
print "=== Modulation: %s ===" % m.modulation_name
print "  Code:                         %s" % code.name
print "  Transmit Spectral Efficiency: %f" % code.tx_eff
print "  Receive Spectral Efficiency:  %f" % code.rx_eff
print "  Required Es/N0:               %f" % code.esn0_db
print "  Required Eb/N0:               %f" % code.req_demod_ebn0_db()

print ""
print "=== System ==="
print "  Transmit Spectral Efficiency: %f" % m.tx_spectral_efficiency_bps_per_hz
print "  Receive Spectral Efficiency:  %f" % m.rx_spectral_efficiency_bps_per_hz
print "  Required Demod Eb/N0:         %f" % m.required_demod_ebn0_db
print "  Implementation Losses:        %f" % m.implementation_loss_db
print "  Required Eb/N0:               %f" % m.required_ebn0_db

print ""
print "Note how the transmit and receive spectral efficiencies are different."
