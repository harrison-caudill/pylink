#!/usr/bin/python

from enum import Enum
import math
import numpy as np


def sequential_enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)


def node_associations(enum):
    node_to_name = {}
    name_to_node = {}
    for key, value, in enum.__dict__.iteritems():
        if not key.startswith('_'):
            node_to_name[value] = key
            name_to_node[key] = value
    return (node_to_name, name_to_node)


def to_db(v):
    return math.log(float(v), 10) * 10


def from_db(v):
    return 10**(float(v)/10.0)


def human_hz(v):
    if v < 1e3:
        return (v, 'Hz')
    if v < 1e6:
        return (v/1.0e3, 'kHz')
    if v < 1e9:
        return (v/1.0e6, 'MHz')
    return (v/1.0e9, 'GHz')


def human_m(v):
    if v < 1e-2:
        return (v*1.0e3, 'mm')
    if v < 1:
        return (v*1.0e2, 'cm')
    if v < 1000:
        return (v, 'm')
    return (v/1.0e3, 'km')


def breakout_metadata(v):
    if isinstance(v, TaggedAttribute):
        return (v.value, v.meta)
    return (v, {})


def spreading_loss_db(dist_km):
    return to_db(4 * math.pi * (dist_km * 1000)**2)


def pattern_generator(peak_gain_dbi, null=-20.0, eff=0.7):
    gain = peak_gain_dbi # just want it called peak_gain_dbi in docs

    # http://www.phys.hawaii.edu/~anita/new/papers/militaryHandbook/antennas.pdf
    X = 75146.0 * (eff-.7) + 41253.0
    bw_3db = (X / gain)**.5
    bw_null = bw_3db*1.5

    # determine step size
    min_n_steps = 25
    step = min(bw_null / min_n_steps, 1.0)
    n = 4.0 * int((360.0 / step) / 4.0) # ensure it is an even multiple of 4
    n_q = int(n / 4)

    def __sigmoid_gen(a=1.0, b=1.0, t=0.0):
        def retval(x):
            return to_db(a / (1.0 + math.exp(-1.0 * b * (x-t)))) + gain
        return retval

    # find the intercept with the null
    sig_upper = 4.0
    sig_lower = -6.0
    a = 1.0
    b = 1.0
    t = (math.log((a/(from_db(null-gain))) - 1) / b) + sig_lower

    sigmoid = np.vectorize(__sigmoid_gen(a=a, b=b, t=t), otypes=[np.float])

    # set things up
    n_half = int(bw_null / step / 2.0)
    sig_step = (sig_upper - sig_lower) / n_half
    main_g_r = np.arange(sig_lower, sig_upper, sig_step)# main lobe, gain, right
    main_a_r = np.arange(0, bw_null, n_half) # main lobe, angles, right
    main_g_r = sigmoid(main_g_r)
    delta = np.arange(0.0, n_half)
    delta *= (gain - main_g_r[-1]) / n_half
    main_g_r += delta

    # combine the left and right sides of the lobe
    main_g_l = list(main_g_r[:])
    main_g_l.reverse()
    main = list(main_g_r) + [gain] + main_g_l

    # combine the main lobe with null for the rest of the pattern
    retval = main + [null]*int(n-len(main))

    # rotate the pattern
    retval = retval[n_half-n_q:] + retval[:n_half-n_q]

    return retval
