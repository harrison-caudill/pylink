#!/usr/bin/python

import math

from ..model import DAGModel
from .. import utils


class Interconnect(object):
    """Provides the specification for the RF chain between two components.

    For example, you might include cabling, connectors, cavity
    filters, and LNAs between a ground-station antenna and a modem.
    You might also create one that specifies the cable between a
    space-side radio module, and space-side antenna module.  Doing it
    this way allows us to specify the rf components on individual
    components, and connections between those components separately.

    Whether or not this interconnect is intended for use on the rx
    side is needed so it can be incorporated in the rx cascade
    calculations or included in the tx inline losses after the PA.

    The overall model assumed here is one of:

    rx_antenna -> rx_interconnect -> receiver

    transmitter -> tx_interconnect -> tx_antenna

    Doing so this way means we have exactly one interconnect per
    budgeted link.
    """

    def __init__(self,
                 name=None,
                 rf_chain=[],
                 is_rx=True):

        # preserve the input
        self.is_rx = is_rx
        self.rf_chain = rf_chain

        if not name:
            name = 'RX Interconnect' if is_rx else 'TX Interconnect'

        self.name = name

        self.tribute = {
            # calculators

            # constants
            self._name('rf_chain'): rf_chain,
            self._name('name'): name,
            }

    def _name(self, s):
        if self.is_rx:
            return 'rx_interconnect_'+s
        else:
            return 'tx_interconnect_'+s
