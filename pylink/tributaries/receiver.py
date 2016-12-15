#!/usr/bin/python

import math

from .. import utils
from .. import element


def _rx_noise_temp_k(model):
    return model.rx_system_noise_temp_k + model.rx_antenna_noise_temp_k


def _rx_system_noise_temp_k(model):
    prev_gain = 1
    retval = 0

    # http://www.microwaves101.com/encyclopedias/noise-figure
    for el in model.rx_rf_chain:

        # Inputs
        el.gain = utils.from_db(el.gain_db)
        el.noise_factor = utils.from_db(el.noise_figure_db)

        el.noise_temp_k = (el.noise_factor-1)*model.room_temp_k

        el.accum_gain = prev_gain * el.gain
        el.noise_temp_contrib = el.noise_temp_k / prev_gain

        # Friis Cascade Equation: F_12 = F1 + (F2-1)/G_1
        # F_1:n = F_n-1 + (F_n-1)/G_1:n-1
        # F_
        el.noise_factor_contrib = (el.noise_factor-1) / prev_gain
        el.prev_gain = prev_gain

        retval += el.noise_temp_contrib
        prev_gain = el.accum_gain

    return retval


def _rx_noise_temp_dbk(model):
    return utils.to_db(model.rx_noise_temp_k)


def _rx_system_noise_factor(model):
    # observing this value ensures that the dependent values are
    # computed and stored
    unused = model.rx_system_noise_temp_k

    return sum([el.noise_factor_contrib for el in model.rx_rf_chain]) + 1


def _rx_system_noise_figure(model):
    return utils.to_db(model.rx_system_noise_factor)


class Receiver(object):

    def __init__(self,
                 rf_chain=None,
                 noise_bw_khz=None,
                 ground_noise_temp_k=290,
                 sky_noise_temp_k=70,
                 room_temp_k=290,
                 implementation_loss_db=0,
                 name='Receiver'):

        if rf_chain is None:
            # RADFACE
            balun = element.Element(name='Balun',
                                    gain_db=-0.9,
                                    noise_figure_db=0.9)
            coax = element.Element(name='Coax',
                                   gain_db=-0.24,
                                   noise_figure_db=0.24)
            lpf = element.Element(name='LFCN',
                                  gain_db=-0.8,
                                  noise_figure_db=0.8)
            sw = element.Element(name='Switch',
                                 gain_db=-0.4,
                                 noise_figure_db=0.4)
            lna = element.Element(name='LNA',
                                  gain_db=22,
                                  noise_figure_db=0.65)
            saw = element.Element(name='SAW Filter',
                                  gain_db=-1.7,
                                  noise_figure_db=1.7)
            rfic = element.Element(name='RFIC',
                                   gain_db=10,
                                   noise_figure_db=6)
            rf_chain = [balun, coax, lpf, sw, lna, saw, rfic]

        noise_bw_hz = noise_bw_khz * 1000 if noise_bw_khz else None

        self.tribute = {
            # calculators
            'rx_noise_temp_k': _rx_noise_temp_k,
            'rx_system_noise_temp_k': _rx_system_noise_temp_k,
            'rx_system_noise_factor': _rx_system_noise_factor,
            'rx_system_noise_figure': _rx_system_noise_figure,
            'rx_noise_temp_dbk': _rx_noise_temp_dbk,

            # constants
            'rx_name': name,
            'receiver_rf_chain': rf_chain,
            'rx_noise_bw_hz': noise_bw_hz,
            'sky_noise_temp_k': sky_noise_temp_k,
            'room_temp_k': room_temp_k,
            'implementation_loss_db': implementation_loss_db,
            }
