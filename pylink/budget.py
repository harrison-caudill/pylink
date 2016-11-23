#!/usr/bin/python

import math

import utils


def _tx_eirp_dbw(model):
    return (model.tx_power_at_antenna_dbw
            + model.tx_antenna_gain_dbi
            - model.tx_antenna_pointing_loss_db)


def _peak_tx_eirp_dbw(model):
    return model.tx_power_at_antenna_dbw + model.tx_antenna_peak_gain_dbi


def _tx_power_at_antenna_dbw(model):
    return model.tx_power_at_pa_dbw - model.tx_inline_losses_db


def _tx_inline_losses_db(model):
    chain = (model.tx_antenna_rf_chain
             + model.tx_interconnect_rf_chain
             + model.transmitter_rf_chain)
    return -1 * sum([c.gain_db for c in chain])


def _rx_rf_chain(model):
    return (model.rx_antenna_rf_chain
            + model.rx_interconnect_rf_chain
            + model.receiver_rf_chain)


def _pf_dbw_per_m2(model):
    spreading = utils.spreading_loss_db(model.slant_range_km)
    return (model.tx_eirp_dbw
            - spreading
            - model.atmospheric_loss_db
            - model.ionospheric_loss_db
            - model.rain_loss_db)


def _compliance_pf_dbw_per_m2(model):
    # this one is here for compliance.  We want to show that under
    # maximum power flux conditions, we can meet our pfd limitations.
    # We ignore things like atmospheric loss and antenna pattern, but
    # we do count slant range.
    spreading = utils.spreading_loss_db(model.periapsis_slant_range_km)
    return (model.peak_tx_eirp_dbw - spreading)


def _peak_pf_dbw_per_m2(model):
    # no matter the tx/rx configuration, the peak pfd is always when
    # the satellite is overhead at the periapsis
    spreading = utils.spreading_loss_db(model.periapsis_altitude_km)

    # The peak EIRP is what we shall consider
    eirp = model.peak_tx_eirp_dbw

    # Regarding occupied bandwidth: The PFD graph assumes that we
    # fully occupy our allocation.  For worst-case, peak PFD purposes,
    # we're going to assume that the currently occupied BW (which
    # should probably be set to the lowest bitrate we'd ever use), is
    # what we'll use.  As such, there is no need to adjust bitrate or
    # anything else.

    # To be conservative, we'll ignore *spheric and rain loss
    return (eirp - spreading)


def _range_to_geo_km(model):
    return model.geo_altitude_km - model.apoapsis_altitude_km


def _peak_pf_at_geo_dbw_per_m2(model):
    if model.is_downlink:
        # the satellite's apoapsis is what we consider
        dist = model.range_to_geo_km
    else:
        dist = model.geo_altitude_km

    spreading = utils.spreading_loss_db(dist)
    return (model.peak_tx_eirp_dbw - spreading)


def _to_hz(model, v):
    return v - utils.to_db(model.required_bw_hz)


def _peak_pfd_at_geo_dbw_per_m2_per_hz(model):
    return _to_hz(model, model.peak_pf_at_geo_dbw_per_m2)


def _compliance_pfd_dbw_per_m2_per_hz(model):
    return _to_hz(model, model.compliance_pf_dbw_per_m2)


def _peak_pfd_at_geo_dbw_per_m2_per_hz(model):
    return _to_hz(model, model.peak_pf_at_geo_dbw_per_m2)


def _peak_pfd_at_geo_dbw_per_m2_per_4khz(model):
    return _to_n_hz(model, model.peak_pfd_at_geo_dbw_per_m2_per_hz, 4e3)


def _pfd_dbw_per_m2_per_hz(model):
    return _to_hz(model, model.pf_dbw_per_m2)

def _to_n_hz(model, base, n):
    return (base + utils.to_db(min(model.required_bw_hz, n)))


def _pfd_dbw_per_m2_per_4khz(model):
    return _to_n_hz(model, model.pfd_dbw_per_m2_per_hz, 4e3)


def _peak_pfd_dbw_per_m2_per_hz(model):
    return _to_hz(model, model.peak_pf_dbw_per_m2)


def _peak_pfd_dbw_per_m2_per_4khz(model):
    return _to_n_hz(model, model.peak_pfd_dbw_per_m2_per_hz, 4e3)


def _rx_power_dbw(model):
    return (model.tx_eirp_dbw
            - model.total_channel_loss_db
            - model.polarization_mismatch_loss_db
            - model.rx_antenna_pointing_loss_db
            + model.rx_antenna_gain_dbi)


def _rx_antenna_effective_area_dbm2(model):
    # Sklar, Page 253, Equation 5.8
    return (model.rx_antenna_gain_dbi
            + utils.to_db(model.wavelength_m**2 / (4 * math.pi)))


def _rx_g_over_t_db(model):
    return model.rx_antenna_gain_dbi - model.rx_noise_temp_dbk


def _rx_n0_dbw_per_hz(model):
    return model.boltzmann_J_per_K_db + model.rx_noise_temp_dbk


def _cn0_db(model):
    return model.rx_power_dbw - model.rx_n0_dbw_per_hz


def _excess_noise_bandwidth_loss_db(model):
    req_bw = model.required_bw_dbhz
    noise_bw = utils.to_db(model.rx_noise_bw_hz) if model.rx_noise_bw_hz else req_bw
    return noise_bw - req_bw


def _rx_eb(model):
    return model.rx_power_dbw - model.bitrate_dbhz


def _rx_ebn0_db(model):
    return model.rx_eb - model.rx_n0_dbw_per_hz


def _required_ebn0_db(model):
            return (model.required_demod_ebn0_db
                    + model.implementation_loss_db
                    + model.excess_noise_bandwidth_loss_db)


def _link_margin_db(model):
    return model.rx_ebn0_db - model.required_ebn0_db


class LinkBudget(object):

    def __init__(self,
                 name='Link Budget',
                 is_downlink=True,
                 rx_antenna_noise_temp_k=300):

        self.tribute = {
            # calculators
            'pf_dbw_per_m2': _pf_dbw_per_m2,
            'compliance_pfd_dbw_per_m2_per_hz': _compliance_pfd_dbw_per_m2_per_hz,
            'peak_pfd_at_geo_dbw_per_m2_per_hz': _peak_pfd_at_geo_dbw_per_m2_per_hz,
            'rx_power_dbw': _rx_power_dbw,
            'rx_antenna_effective_area_dbm2': _rx_antenna_effective_area_dbm2,
            'rx_g_over_t_db': _rx_g_over_t_db,
            'rx_n0_dbw_per_hz': _rx_n0_dbw_per_hz,
            'cn0_db': _cn0_db,
            'excess_noise_bandwidth_loss_db': _excess_noise_bandwidth_loss_db,
            'pfd_dbw_per_m2_per_4khz': _pfd_dbw_per_m2_per_4khz,
            'pfd_dbw_per_m2_per_hz': _pfd_dbw_per_m2_per_hz,
            'rx_eb': _rx_eb,
            'rx_ebn0_db': _rx_ebn0_db,
            'link_margin_db': _link_margin_db,
            'peak_pf_at_geo_dbw_per_m2': _peak_pf_at_geo_dbw_per_m2,
            'boltzmann_J_per_K': 1.3806488e-23,
            'boltzmann_J_per_K_db': utils.to_db(1.3806488e-23),
            'peak_pf_at_geo_dbw_per_m2': _peak_pf_at_geo_dbw_per_m2,
            'peak_pfd_at_geo_dbw_per_m2_per_4khz': _peak_pfd_at_geo_dbw_per_m2_per_4khz,
            'peak_pf_dbw_per_m2': _peak_pf_dbw_per_m2,
            'peak_pfd_dbw_per_m2_per_4khz': _peak_pfd_dbw_per_m2_per_4khz,
            'compliance_pf_dbw_per_m2': _compliance_pf_dbw_per_m2,
            'range_to_geo_km': _range_to_geo_km,
            'rx_rf_chain': _rx_rf_chain,
            'tx_inline_losses_db': _tx_inline_losses_db,
            'tx_power_at_antenna_dbw': _tx_power_at_antenna_dbw,
            'tx_eirp_dbw': _tx_eirp_dbw,
            'peak_tx_eirp_dbw': _peak_tx_eirp_dbw,
            'required_ebn0_db': _required_ebn0_db,

            # constants
            'budget_name': name,
            'boltzmann_J_per_K': 1.3806488e-23,
            'boltzmann_J_per_K_db': utils.to_db(1.3806488e-23),
            'is_downlink': is_downlink,
            'rx_antenna_noise_temp_k': rx_antenna_noise_temp_k,
            }
