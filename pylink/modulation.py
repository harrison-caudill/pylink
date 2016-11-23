#!/usr/bin/python

import math
from collections import OrderedDict

import utils


class Code(object):

    def __init__(self, name, tx_eff, rx_eff, esn0):
        self.name = name
        self.tx_eff = tx_eff
        self.rx_eff = rx_eff
        self.esn0 = esn0
        self.req_cn0 = None

    def req_demod_ebn0_db(self):
        return self.rx_eff * self.esn0


# http://www.etsi.org/deliver/etsi_en/302300_302399/30230702/01.01.01_20
#       /en_30230702v010101a.pdf
# Page 52
NORMAL_DVBS2X_PERFORMANCE = {
    "QPSK 2/9": Code("QPSK 2/9", 0.434841, 0.434841, -2.850000),
    "QPSK 13/45": Code("QPSK 13/45", 0.567805, 0.567805, -2.030000),
    "QPSK 9/20": Code("QPSK 9/20", 0.889135, 0.889135, 0.220000),
    "QPSK 11/20": Code("QPSK 11/20", 1.088581, 1.088581, 1.450000),
    "8APSK 5/9-L": Code("8APSK 5/9-L", 1.647211, 1.647211, 4.730000),
    "8APSK 26/45-L": Code("8APSK 26/45-L", 1.713601, 1.713601, 5.130000),
    "8PSK 23/36": Code("8PSK 23/36", 1.896173, 1.896173, 6.120000),
    "8PSK 25/36": Code("8PSK 25/36", 2.062148, 2.062148, 7.020000),
    "8PSK 13/18": Code("8PSK 13/18", 2.145136, 2.145136, 7.490000),
    "16APSK 1/2-L": Code("16APSK 1/2-L", 1.972253, 1.972253, 5.970000),
    "16APSK 8/15-L": Code("16APSK 8/15-L", 2.104850, 2.104850, 6.550000),
    "16APSK 5/9-L": Code("16APSK 5/9-L", 2.193247, 2.193247, 6.840000),
    "16APSK 26/45": Code("16APSK 26/45", 2.281645, 2.281645, 7.510000),
    "16APSK 3/5": Code("16APSK 3/5", 2.370043, 2.370043, 7.800000),
    "16APSK 3/5-L": Code("16APSK 3/5-L", 2.370043, 2.370043, 7.410000),
    "16APSK 28/45": Code("16APSK 28/45", 2.458441, 2.458441, 8.100000),
    "16APSK 23/36": Code("16APSK 23/36", 2.524739, 2.524739, 8.380000),
    "16APSK 2/3-L": Code("16APSK 2/3-L", 2.635236, 2.635236, 8.430000),
    "16APSK 25/36": Code("16APSK 25/36", 2.745734, 2.745734, 9.270000),
    "16APSK 13/18": Code("16APSK 13/18", 2.856231, 2.856231, 9.710000),
    "16APSK 7/9": Code("16APSK 7/9", 3.077225, 3.077225, 10.650000),
    "16APSK 77/90": Code("16APSK 77/90", 3.386618, 3.386618, 11.990000),
    "32APSK 2/3-L": Code("32APSK 2/3-L", 3.289502, 3.289502, 11.100000),
    "32APSK 32/45": Code("32APSK 32/45", 3.510192, 3.510192, 11.750000),
    "32APSK 11/15": Code("32APSK 11/15", 3.620536, 3.620536, 12.170000),
    "32APSK 7/9": Code("32APSK 7/9", 3.841226, 3.841226, 13.050000),
    "64APSK 32/45-L": Code("64APSK 32/45-L", 4.206428, 4.206428, 13.980000),
    "64APSK 11/15": Code("64APSK 11/15", 4.338659, 4.338659, 14.810000),
    "64APSK 7/9": Code("64APSK 7/9", 4.603122, 4.603122, 15.470000),
    "64APSK 4/5": Code("64APSK 4/5", 4.735354, 4.735354, 15.870000),
    "64APSK 5/6": Code("64APSK 5/6", 4.933701, 4.933701, 16.550000),
    "128APSK 3/4": Code("128APSK 3/4", 5.163248, 5.163248, 17.730000),
    "128APSK 7/9": Code("128APSK 7/9", 5.355556, 5.355556, 18.530000),
    "256APSK 29/45-L": Code("256APSK 29/45-L", 5.065690, 5.065690, 16.980000),
    "256APSK 2/3-L": Code("256APSK 2/3-L", 5.241514, 5.241514, 17.240000),
    "256APSK 31/45-L": Code("256APSK 31/45-L", 5.417338, 5.417338, 18.100000),
    "256APSK 32/45": Code("256APSK 32/45", 5.593162, 5.593162, 18.590000),
    "256APSK 11/15-L": Code("256APSK 11/15-L", 5.768987, 5.768987, 18.840000),
    "256APSK 3/4": Code("256APSK 3/4", 5.900855, 5.900855, 19.570000),
    }


def _modulation_lookup_table(model):
    table = []
    allocation = model.allocation_hz
    for name, code in model.modulation_performance_table.iteritems():
        bitrate = allocation / code.tx_eff
        cn0 = utils.to_db(bitrate) + code.req_demod_ebn0_db()
        table.append((cn0, code))
        code.req_cn0 = cn0
    return OrderedDict(table)


def _best_modulation_code(model):
    cn0 = model.cn0_db - model.target_margin_db
    table = model.modulation_lookup_table
    keys = table.keys()
    keys.sort()
    best_option = table[keys[0]]
    for req_cn0 in keys:
        code = table[req_cn0]
        if cn0 >= req_cn0:
            best_option = code
    return best_option


def _rx_spectral_efficiency_bps_per_hz(model):
    return model.best_modulation_code.rx_eff


def _tx_spectral_efficiency_bps_per_hz(model):
    return model.best_modulation_code.tx_eff


def _required_demod_ebn0_db(model):
    return model.best_modulation_code.req_demod_ebn0_db()


class Modulation(object):

    def __init__(self, name='DVB-S2X', perf=NORMAL_DVBS2X_PERFORMANCE):

        self.tribute = {
            # calculators
            'required_demod_ebn0_db': _required_demod_ebn0_db,
            'modulation_lookup_table': _modulation_lookup_table,
            'best_modulation_code': _best_modulation_code,
            'tx_spectral_efficiency_bps_per_hz': _tx_spectral_efficiency_bps_per_hz,
            'rx_spectral_efficiency_bps_per_hz': _rx_spectral_efficiency_bps_per_hz,

            # constants
            'modulation_name': name,
            'modulation_performance_table': perf,
            }
