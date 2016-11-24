#!/usr/bin/python

import math

import utils


class Code(object):

    def __init__(self, name, tx_eff, rx_eff, esn0_db):
        self.name = name
        self.tx_eff = tx_eff
        self.rx_eff = rx_eff
        self.esn0_db = esn0_db

        # cached values
        self.saturating_cn0 = None
        self.max_unconstrained_bitrate = None
        self.max_constrained_bitrate = None

    def req_demod_ebn0_db(self):
        return self.esn0_db - utils.to_db(self.rx_eff)


# http://www.etsi.org/deliver/etsi_en/302300_302399/30230702/01.01.01_20
#       /en_30230702v010101a.pdf
# Page 52
# One notable exception is that the transmit spectral efficiency
# defaults to 0.8 * the receive spectral efficiency to leave room for
# rolloff.  Feel free to override
NORMAL_DVBS2X_PERFORMANCE = [
    Code("QPSK 2/9", 0.347873, 0.434841, -2.850000),
    Code("QPSK 13/45", 0.454244, 0.567805, -2.030000),
    Code("QPSK 9/20", 0.711308, 0.889135, 0.220000),
    Code("QPSK 11/20", 0.870865, 1.088581, 1.450000),
    Code("8APSK 5/9-L", 1.317769, 1.647211, 4.730000),
    Code("8APSK 26/45-L", 1.370881, 1.713601, 5.130000),
    Code("8PSK 23/36", 1.516938, 1.896173, 6.120000),
    Code("8PSK 25/36", 1.649718, 2.062148, 7.020000),
    Code("8PSK 13/18", 1.716109, 2.145136, 7.490000),
    Code("16APSK 1/2-L", 1.577802, 1.972253, 5.970000),
    Code("16APSK 8/15-L", 1.683880, 2.104850, 6.550000),
    Code("16APSK 5/9-L", 1.754598, 2.193247, 6.840000),
    Code("16APSK 26/45", 1.825316, 2.281645, 7.510000),
    Code("16APSK 3/5", 1.896034, 2.370043, 7.800000),
    Code("16APSK 3/5-L", 1.896034, 2.370043, 7.410000),
    Code("16APSK 28/45", 1.966753, 2.458441, 8.100000),
    Code("16APSK 23/36", 2.019791, 2.524739, 8.380000),
    Code("16APSK 2/3-L", 2.108189, 2.635236, 8.430000),
    Code("16APSK 25/36", 2.196587, 2.745734, 9.270000),
    Code("16APSK 13/18", 2.284985, 2.856231, 9.710000),
    Code("16APSK 7/9", 2.461780, 3.077225, 10.650000),
    Code("16APSK 77/90", 2.709294, 3.386618, 11.990000),
    Code("32APSK 2/3-L", 2.631602, 3.289502, 11.100000),
    Code("32APSK 32/45", 2.808154, 3.510192, 11.750000),
    Code("32APSK 11/15", 2.896429, 3.620536, 12.170000),
    Code("32APSK 7/9", 3.072981, 3.841226, 13.050000),
    Code("64APSK 32/45-L", 3.365142, 4.206428, 13.980000),
    Code("64APSK 11/15", 3.470927, 4.338659, 14.810000),
    Code("64APSK 7/9", 3.682498, 4.603122, 15.470000),
    Code("64APSK 4/5", 3.788283, 4.735354, 15.870000),
    Code("64APSK 5/6", 3.946961, 4.933701, 16.550000),
    Code("128APSK 3/4", 4.130598, 5.163248, 17.730000),
    Code("128APSK 7/9", 4.284445, 5.355556, 18.530000),
    Code("256APSK 29/45-L", 4.052552, 5.065690, 16.980000),
    Code("256APSK 2/3-L", 4.193211, 5.241514, 17.240000),
    Code("256APSK 31/45-L", 4.333870, 5.417338, 18.100000),
    Code("256APSK 32/45", 4.474530, 5.593162, 18.590000),
    Code("256APSK 11/15-L", 4.615190, 5.768987, 18.840000),
    Code("256APSK 3/4", 4.720684, 5.900855, 19.570000),
    ]


def __max_bitrate_hz(cn0_db,
                     additional_rx_losses_db,
                     target_margin_db,
                     required_ebn0_db):
    cn0 = cn0_db - additional_rx_losses_db - target_margin_db
    ebn0 = required_ebn0_db
    return utils.from_db(cn0 - ebn0)


def _modulation_code_lookup_table(model):
    e = model.enum

    allocation = model.allocation_hz

    best_option = None
    best_bitrate = -1

    retval = {}

    for code in model.modulation_performance_table:
        max_constrained = allocation * code.tx_eff
        code.max_constrained_bitrate = max_constrained
        code.saturating_cn0 = code.req_demod_ebn0_db() * max_constrained

        retval[max_constrained] = code

    return retval


def _best_modulation_code(model):
    e = model.enum

    allocation = model.allocation_hz
    cn0_db = model.cn0_db
    implementation_loss_db = model.implementation_loss_db
    target_margin_db = model.target_margin_db


    # DANGER WILL ROBINSON!!
    model.override(e.best_modulation_code,model.modulation_performance_table[0])
    added_loss = model.cached_calculate(e.additional_rx_losses_db,
                                        clear_stack=True)
    model.revert(e.best_modulation_code)
    # DANGER WILL ROBINSON!!


    best_option = None
    best_bitrate = -1

    for sat_cn0, code in model.modulation_code_lookup_table.iteritems():
        max_unconstrained = __max_bitrate_hz(cn0_db,
                                             added_loss,
                                             target_margin_db,
                                             code.req_demod_ebn0_db())
        R = min(max_unconstrained, code.max_constrained_bitrate)

        if R > best_bitrate:
            best_option = code
            best_bitrate = R

    return best_option


def _rx_spectral_efficiency_bps_per_hz(model):
    return model.best_modulation_code.rx_eff


def _tx_spectral_efficiency_bps_per_hz(model):
    return model.best_modulation_code.tx_eff


def _required_demod_ebn0_db(model):
    return model.best_modulation_code.req_demod_ebn0_db()


def _max_bitrate_hz(model):
    return __max_bitrate_hz(model.cn0_db,
                            model.additional_rx_losses_db,
                            model.target_margin_db,
                            model.required_ebn0_db)


class Modulation(object):

    def __init__(self, name='DVB-S2X', perf=NORMAL_DVBS2X_PERFORMANCE):

        self.tribute = {
            # calculators
            'required_demod_ebn0_db': _required_demod_ebn0_db,
            'best_modulation_code': _best_modulation_code,
            'tx_spectral_efficiency_bps_per_hz': _tx_spectral_efficiency_bps_per_hz,
            'rx_spectral_efficiency_bps_per_hz': _rx_spectral_efficiency_bps_per_hz,
            'max_bitrate_hz': _max_bitrate_hz,
            'modulation_code_lookup_table': _modulation_code_lookup_table,

            # constants
            'modulation_name': name,
            'modulation_performance_table': perf,
            }
