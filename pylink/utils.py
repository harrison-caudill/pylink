#!/usr/bin/python

from enum import Enum
import math
import numpy as np


def sequential_enum(*sequential, **named):
    """Returns a new enum with all given named and sequential nodes.

    sequential -- [str, str, ...]
    named -- str:int
    """
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)


def node_associations(enum):
    """Returns dicts associating nodes -> names and vice versa from an enum.

    Given an enum, returns the dict of names to numbers and numbers to
    names.
    """
    node_to_name = {}
    name_to_node = {}
    for key, value, in enum.__dict__.items():
        if not key.startswith('_'):
            node_to_name[value] = key
            name_to_node[key] = value
    return (node_to_name, name_to_node)


def to_db(v):
    """linear to dB
    """
    return math.log(float(v), 10) * 10


def from_db(v):
    """dB to linear
    """
    return 10**(float(v)/10.0)


def human_hz(v):
    """Returns a number of Hz autoselected for Hz, kHz, MHz, and GHz
    """
    if v < 1e3:
        return (v, 'Hz')
    if v < 1e6:
        return (v/1.0e3, 'kHz')
    if v < 1e9:
        return (v/1.0e6, 'MHz')
    return (v/1.0e9, 'GHz')


def human_m(v):
    """Returns a distance autoselected for mm, cm, m, and km
    """
    if v < 1e-2:
        return (v*1.0e3, 'mm')
    if v < 1:
        return (v*1.0e2, 'cm')
    if v < 1000:
        return (v, 'm')
    return (v/1.0e3, 'km')


def human_b(bytes):
    """Returns a number of bytes autoselected for kB, MB, GB, TB

    Just to be clear, this will use the 1024 versions, not the 1000
    versions.
    """
    suffixes = ['EB', 'PB', 'TB', 'GB', 'MB', 'kB']
    n = len(suffixes)
    for i in range(n):
        m = 1<<(10*(n-i))
        if bytes > m:
            print(math.log(bytes, 2), bytes / float(m), suffixes[i])
            return (bytes / float(m), suffixes[i])
    return (bytes, 'B')


def spreading_loss_db(dist_km):
    """Returns the loss, in dB, associated with distance alone.
    """
    return to_db(4 * math.pi * (dist_km * 1000)**2)


def rx_pfd_hz_adjust(model, base, n):
    """Transforms a PF into a PFD at N Hz for Rx
    """
    return pfd_hz_manual_adjust(base, model.required_rx_bw_hz, n)


def tx_pfd_hz_adjust(model, base, n):
    """Transforms a PF into a PFD at N Hz for Tx
    """
    return pfd_hz_manual_adjust(base, model.required_tx_bw_hz, n)


def pfd_hz_manual_adjust(base, occ, n):
    """Transforms a PF into a PFD at N Hz for Rx assuming occ BW
    """

    n_db = to_db(n)
    occ_db = to_db(occ)
    if n_db > occ_db:
        return base
    else:
        return base - occ_db + n_db


def pattern_generator(peak_gain_dbi, null=-20.0, eff=0.7):
    """Generates a sample antenna pattern.

    The pattern will be a main lobe, and the rest will be the <null>
    value.

    FIXME: See if a reasonable pattern, including side-lobes, can be
           generated easily

    peak_gain_dbi -- float
    null -- float, value outside of the main lobe
    eff -- float, antenna efficiency value
    """
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

    # find the peak
    n_rot = 0
    peak = min(retval)
    for i in range(len(retval)):
        if retval[i] > peak:
            n_rot = i
            peak = retval[i]

    # rotate the pattern
    retval = retval[n_rot:] + retval[:n_rot]

    return retval


def eirp_dbw_to_e_field_v_per_m(eirp_dbw, dist_m):
    """Returns the E field strength at a given distance/eirp

    The resulting value is in volts per meter, linear units.  The EIRP
    should be in dBW.
    """
    # http://www.ti.com/lit/an/swra048/swra048.pdf
    # https://www.craf.eu/useful-equations/conversion-formulae/
    # (PG)/(4*pi*d^2) = (E^2)/(120*pi)
    # eirp/(4*pi*d^2) = (E^2)/(120*pi)
    # E^2 = eirp * 120 * pi / 4 * pi * d^2
    # E^2 = eirp * 30 / d^2
    # E = (eirp * 30 / d^2) ^0.5
    # E = (eirp * 30) ^ 0.5 / d
    # E = (eirp * 30) ^ 0.5 / d

    E_db = ((eirp_dbw + to_db(30)) / 2) - to_db(dist_m)
    E = from_db(E_db)
    return E


def e_field_to_eirp_dbw(E, dist_m):
    """Returns the EIRP required to create a given E field strength.

    E field strength is in linear units, volts per meter.  The
    resulting value is in dBW.
    """
    # http://www.ti.com/lit/an/swra048/swra048.pdf
    # eirp = to_db(E^2 * dist_m^2 / 0.03)
    # https://www.craf.eu/useful-equations/conversion-formulae/
    # (PG)/(4*pi*d^2) = (E^2)/(120*pi)
    # eirp/(4*pi*d^2) = (E^2)/(120*pi)
    # eirp = (E^2) * (4*pi*d^2) / (120*pi)
    # eirp = (E^2 * d^2 * 4 * pi) / (120 * pi)
    # eirp = (E^2 * d^2) / 30

    eirp = E**2 * dist_m**2 / 30
    return to_db(eirp)
