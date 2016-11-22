#!/usr/bin/python

import math

import utils


class Modulation(object):

    def __init__(self,
                 name,
                 required_ebn0_db=10.4,
                 spectral_efficiency_bps_per_hz=1,
                 bits_per_symbol=1):

        self.tribute = {
            # calculators

            # constants
            'modulation_name': name,
            'required_demod_ebn0_db': required_ebn0_db,
            'spectral_efficiency_bps_per_hz': spectral_efficiency_bps_per_hz,
            'bits_per_symbol': bits_per_symbol,
            }
