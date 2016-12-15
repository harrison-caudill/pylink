#!/usr/bin/python

import math

from .. import utils


def _unity_gain_propagation_loss_db(model):
    # Sklar, page 254, Equation 5.10
    d = model.slant_range_km * 1000
    lam = model.wavelength_m
    return 2 * utils.to_db(4 * math.pi * d / lam)


def _allocation_start_hz(model):
    return model.center_freq_hz - (model.allocation_hz/2)


def _allocation_end_hz(model):
    return model.center_freq_hz + (model.allocation_hz/2)


def _total_channel_loss_db(model):
    return (model.unity_gain_propagation_loss_db
            + model.atmospheric_loss_db
            + model.ionospheric_loss_db
            + model.rain_loss_db
            + model.multipath_fading_db)


def _required_tx_bw_hz(model):
    return model.bitrate_hz / model.tx_spectral_efficiency_bps_per_hz


def _required_rx_bw_hz(model):
    return model.bitrate_hz / model.rx_spectral_efficiency_bps_per_hz


def _required_tx_bw_dbhz(model):
    return utils.to_db(model.required_tx_bw_hz)


def _required_rx_bw_dbhz(model):
    return utils.to_db(model.required_rx_bw_hz)


def _wavelength_m(model):
    return model.speed_of_light_m_per_s / model.center_freq_hz


def _bitrate_dbhz(model):
    return utils.to_db(model.bitrate_hz)


class Channel(object):

    def __init__(self,
                 center_freq_mhz=402.7,
                 bitrate_hz=9600,
                 atmospheric_loss_db=0.5,
                 ionospheric_loss_db=0.5,
                 rain_loss_db=0.5,
                 multipath_fading_db=0,
                 allocation_hz=10e6,
                 speed_of_light_m_per_s=299792458.00,
                 polarization_mismatch_loss_db=3.0,
                 gs_pfd_limits=None):

        # FIXME: Consider calculating polarization mismatch loss from
        # angle, including axial ratio, ...

        self.tribute = {
            # calculators
            'unity_gain_propagation_loss_db': _unity_gain_propagation_loss_db,
            'total_channel_loss_db': _total_channel_loss_db,
            'wavelength_m': _wavelength_m,
            'bitrate_dbhz': _bitrate_dbhz,
            'required_tx_bw_hz': _required_tx_bw_hz,
            'required_rx_bw_hz': _required_rx_bw_hz,
            'required_tx_bw_dbhz': _required_tx_bw_dbhz,
            'required_rx_bw_dbhz': _required_rx_bw_dbhz,
            'allocation_start_hz': _allocation_start_hz,
            'allocation_end_hz': _allocation_end_hz,
            
            # constants
            'center_freq_hz': center_freq_mhz * 1e6,
            'bitrate_hz': bitrate_hz,
            'atmospheric_loss_db': atmospheric_loss_db,
            'ionospheric_loss_db': ionospheric_loss_db,
            'rain_loss_db': rain_loss_db,
            'multipath_fading_db': multipath_fading_db,
            'speed_of_light_m_per_s': speed_of_light_m_per_s,
            'polarization_mismatch_loss_db': polarization_mismatch_loss_db,
            'allocation_hz': allocation_hz,
            'gs_pfd_limits': gs_pfd_limits,
            }
