#!/usr/bin/python

import math

from .. import utils


class Transmitter(object):

    def __init__(self,
                 tx_power_at_pa_dbw=3,
                 rf_chain=[],
                 name='Transmitter'):

        self.tribute = {
            # calculators

            # constants
            'transmitter_rf_chain': rf_chain,
            'transmitter_name': name,
            'tx_power_at_pa_dbw': tx_power_at_pa_dbw,
            }
