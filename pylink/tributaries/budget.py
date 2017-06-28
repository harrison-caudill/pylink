#!/usr/bin/python

import types
import math
import jinja2
import os
from jinja2 import Template
import numpy as np
import matplotlib.pyplot as plt
import collections

from model import DAGModel
from tagged_attribute import TaggedAttribute
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
    spreading = utils.spreading_loss_db(model.perigee_slant_range_km)
    return (model.peak_tx_eirp_dbw - spreading)


def _peak_pf_dbw_per_m2(model):
    # no matter the tx/rx configuration, the peak pfd is always when
    # the satellite is overhead at the perigee
    spreading = utils.spreading_loss_db(model.perigee_altitude_km)

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
    return model.geo_altitude_km - model.apogee_altitude_km


def _peak_pf_at_geo_dbw_per_m2(model):
    if model.is_downlink:
        # the satellite's apogee is what we consider
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
    return _to_hz(model, model.peak_pfd_at_geo_dbw_per_m2)


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


class PFDFigure(object):

    def _plot_peak_pfd(self):
        m = self.model
        e = self.model.enum

        occ_bw = self.model.required_bw_hz
        if self.is_gso:
            pfd_per_hz = m.peak_pfd_at_geo_dbw_per_m2_per_hz
        else:
            pfd_per_hz = m.peak_pf_dbw_per_m2_per_hz
        pfd_per_hz = peak_pf - utils.to_db(occ_bw)

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        n = int(self.end_hz) - int(self.start_hz)
        x = np.linspace(1, n, n-1)
        x += self.start_hz
        y = np.zeros(n-1)
        y += pfd_per_hz
        for i in range(len(x)):
            bw = min(x[i], occ_bw)
            y[i] += _to_n_hz(m, pfd_per_hz, bw)
        ax.plot(x, y, color='b', label='PFD (dBW/m^2)')

        ax.set_xlabel('Bandwidth (Hz)')
        if self.is_gso:
            ax.set_ylabel('PFD at GSO(dBW/m^2')
        else:
            ax.set_ylabel('PFD at Receiver (dBW/m^2)')
        plt.savefig(self.fname(), transparent=True)

    def _plot_pfd_at_receiver(self):
        m = self.model
        e = self.model.enum

        orig_el = m.override_value(e.min_elevation_deg)

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        if self.pfd_limits:
            x = [p[0] for p in self.pfd_limits]
            y = [p[1] for p in self.pfd_limits]
            ax.plot(x, y, color='r', linewidth=2, label='Limit')

        x = np.linspace(0.0, 90.0, 90)
        y = np.linspace(0.0, 90.0, 90)
        for i in range(len(x)):
            m.override(e.min_elevation_deg, x[i])
            y[i] = (m.compliance_pf_dbw_per_m2
                    + utils.to_db(self.bw)
                    - m.required_bw_dbhz)
        ax.plot(x, y, color='b')
        ax.set_xlabel('Elevation Angle (degrees) above Earth Horizon')
        ax.set_ylabel('PFD (dBW/m^2/4KHz')

        if self.pfd_limits:
            upper = max(max(y), self.pfd_limits[-1][1])
            lower = min(min(y), self.pfd_limits[0][1])
        else:
            upper = max(y)
            lower = min(y)
        delta = upper - lower
        upper += delta*0.1
        lower -= delta*0.1

        plt.ylim(lower, upper)
        plt.grid()
        fig.savefig(self.fname(), transparent=True)
        if orig_el is not None:
            m.override(e.min_elevation_deg, orig_el)
        else:
            m.reset(e.min_elevation_deg)

    def plot(self):
        if self.is_bw:
            self._plot_peak_pfd()
        else:
            self._plot_pfd_at_receiver()

    def fname(self):
        prefix = 'gso' if self.is_gso else 'rx'
        prefix = 'pfd-' + prefix
        if self.is_bw:
            return '%s_%d-%d.png' % (prefix, self.start_hz, self.end_hz)
        else:
            return 'rx-vsEl.png'

    def label(self):
        prefix = 'gso' if self.is_gso else 'rx'
        if self.is_bw:
            return '%s_%d-%d' % (prefix, self.start_hz, self.end_hz)
        else:
            return 'rx-vsEl'

    def caption(self):
        if self.is_bw:
            if self.is_gso:
                return 'Peak PFD at GSO vs Bandwidth'
            else:
                if self.budget.is_downlink:
                    return 'Peak PFD at Surface vs Bandwidth'
                else:
                    return 'Peak PFD at Receiver vs Bandwidth'
        else:
            return 'PFD at Receiver'

    def to_latex(self):
        return '''
  \\begin{figure}
    \\caption{%s}
    \\includegraphics[width=\\linewidth]{%s}
    \\label{fig::pfd::%s}
  \\end{figure}
        ''' % (self.caption(), self.fname(), self.label())

    def __init__(self,
                 budget,
                 is_bw=True,
                 start_hz=0,
                 bw=4e3,
                 end_hz=4e3,
                 is_gso=False,
                 pfd_limits=None):
        self.is_bw = is_bw
        self.start_hz = start_hz
        self.end_hz = end_hz
        self.is_gso = is_gso
        self.budget = budget
        self.model = budget.model
        self.enum = self.model.enum
        self.pfd_limits = pfd_limits
        self.bw = bw


class BitrateFigure(object):

    def plot(self):
        m = self.model
        e = self.model.enum

        orig_el = m.min_elevation_deg
        orig_margin = m.override_value(e.link_margin_db)

        # get our boundaries
        start_bitrate = m.bitrate_dbhz + m.link_margin_db - self.margin_db
        start_pf = m.pf_dbw_per_m2

        min_angle = 0
        min_pf = m.pf_dbw_per_m2
        min_bitrate = m.bitrate_dbhz

        max_angle = 0
        max_pf = m.pf_dbw_per_m2
        max_bitrate = m.bitrate_dbhz

        for i in range(91):
            m.override(e.min_elevation_deg, i)
            pf = m.pf_dbw_per_m2
            pf_delta = pf - start_pf
            bitrate = start_bitrate + pf_delta

            if min_pf > pf:
                min_pf = pf
                min_angle = i
                min_bitrate = bitrate

            if max_pf < pf:
                max_pf = pf
                max_angle = i
                max_bitrate = bitrate

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)

        x = np.linspace(0.0, 90.0, 90)
        y = np.linspace(0.0, 90.0, 90)
        unit = None
        for i in range(len(x)):
            m.override(e.min_elevation_deg, x[i])
            start = utils.from_db(min_bitrate)*.9
            stop = utils.from_db(max_bitrate)*1.1
            step = (stop - start) / self.n_steps

            bitrate = m.solve_for(e.bitrate_hz,
                                  e.link_margin_db, self.margin_db,
                                  start, stop, step,
                                  rounds=4)
            (R, unit,) = utils.human_hz(bitrate)
            y[i] = R

        ax.plot(x, y, color='b')
        ax.set_xlabel('Elevation Angle (degrees)')
        ax.set_ylabel('Bitrate (%s)' % unit)

        upper = max(y)
        lower = min(y)
        delta = upper - lower
        upper += delta*0.1
        lower -= delta*0.1

        plt.ylim(lower, upper)
        fig.savefig(self.fname(), transparent=True)

        m.override(e.min_elevation_deg, orig_el)
        if orig_margin is not None:
            m.override(e.link_margin_db, orig_margin)

    def fname(self):
        return 'bitrate.png'

    def label(self):
        return 'bitrate'

    def caption(self):
        return 'Bitrate with %ddB of Link Margin vs Elevation' % self.margin_db

    def to_latex(self):
        return '''
  \\begin{figure}
    \\caption{%s}
    \\includegraphics[width=\\linewidth]{%s}
    \\label{fig::pfd::%s}
  \\end{figure}
        ''' % (self.caption(), self.fname(), self.label())


    def __init__(self, budget, margin_db=2, n_steps=200):
        self.budget = budget
        self.model = self.budget.model
        self.enum = self.model.enum
        self.margin_db = margin_db
        self.n_steps = n_steps


class LinkBudget(object):

    def __init__(self,
                 defaults=[],
                 enum=None,
                 name='Link Budget',
                 is_downlink=True,
                 **extras):
        if enum is None:
            enum = utils.sequential_enum(*[])

        tmp = {}
        tmp.update({
            'budget_name': name,
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
            'boltzmann_J_per_K': 1.3806488e-23,
            'boltzmann_J_per_K_db': utils.to_db(1.3806488e-23),
            'peak_pf_at_geo_dbw_per_m2': _peak_pf_at_geo_dbw_per_m2,
            'peak_pfd_at_geo_dbw_per_m2_per_4khz': _peak_pfd_at_geo_dbw_per_m2_per_4khz,
            'peak_pf_dbw_per_m2': _peak_pf_dbw_per_m2,
            'is_downlink': is_downlink,
            'peak_pfd_dbw_per_m2_per_4khz': _peak_pfd_dbw_per_m2_per_4khz,
            'compliance_pf_dbw_per_m2': _compliance_pf_dbw_per_m2,
            'range_to_geo_km': _range_to_geo_km,
            'rx_rf_chain': _rx_rf_chain,
            'tx_inline_losses_db': _tx_inline_losses_db,
            'tx_power_at_antenna_dbw': _tx_power_at_antenna_dbw,
            'tx_eirp_dbw': _tx_eirp_dbw,
            'peak_tx_eirp_dbw': _peak_tx_eirp_dbw,
            'rx_antenna_noise_temp_k': 300,
            'required_ebn0_db': _required_ebn0_db,
            })
        tmp.update(extras)
        extras = tmp

        # calculate the list of node names & enum
        self.name_list = []
        map(lambda x: self.name_list.extend(x.tribute.keys()), defaults)
        self.name_list.extend(extras.keys())
        self.enum = utils.sequential_enum(*self.name_list)

        # map the names to nodes, etc
        (self.node_to_name,
         self.name_to_node,) = utils.node_associations(self.enum)

        # self.dependencies = {}
        self.overrides = {}
        self.calculators = {}

        tributes = [m.tribute for m in defaults]
        tributes.append(extras)
        for t in tributes:
            for name, v, in t.iteritems():
                if hasattr(v, '__call__'):
                    self.calculators[self.name_to_node[name]] = v
                else:
                    self.overrides[self.name_to_node[name]] = v

        self.model = DAGModel(self.calculators,
                              self.enum,
                              {},)
        for k, v in self.overrides.iteritems():
            if isinstance(v, TaggedAttribute):
                self.model.set_meta(k, **v.meta)
                self.model.override(k, v.value)
            else:
                self.model.override(k, v)

    def _table(self, items, use_headers=True):
        m = self.model
        table = ''
        table += '\\begin{tabular}{p{3in}p{1in}l}\n'
        for section in items:
            s = section
            if section == 'Transmitter': s = 'Transmitter (%s)' % m.transmitter_name
            if section == 'Receiver': s = 'Receiver (%s)' % m.rx_name
            if use_headers:
                table += '\\textbf{%s} & & \\\\\n' % s
                table += '\\hline \\\\\n'
            lines = items[section]
            for line in lines:
                v = line[1]
                v = '%.2f' % v if isinstance(v, float) else '%s' % v
                table += '%s & %s & $%s$ \\\\\n' % (line[0],
                                                    v,
                                                    line[2])
            table += '\\\\\n'

        table += '\\end{tabular}\n'
        return table

    def _rx_chain_table(self):
        m = self.model
        e = m.enum
        chain = m.rx_rf_chain

        fields = [('Element', '', 1.25),
                  ('Gain', 'dB', .35),
                  ('Noise Figure', 'dB', .47),
                  ('Noise Temp.', 'K', .5),
                  ('Upstream Accum. Gain', '', .6),
                  ('Noise Temp Contrib.', 'K', .5),
                  ('Noise Factor Contrib.', '', .5),
                  ('Noise Temp Contrib. Pct', '\\%', .75),
                  ]

        field_definitions = ''.join(['p{%sin}' % f[-1] for f in fields])
        table = ['\\hspace*{-0.75in} \\begin{tabular}{%s}' % field_definitions]

        # titles
        row = ['\\textbf{%s}' % f[0] for f in fields]
        table.append(' & '.join(row) + '\\\\')
        table.append('\hline \\\\')

        # Units
        row = []
        for f in fields:
            if len(f[1]):
                row.append('\\textbf{$%s$}' % (f[1]))
            else:
                row.append('')
        table.append(' & '.join(row) + '\\\\')
        table.append('\hline \\\\')


        for el in chain:
            pct = el.noise_temp_contrib / m.rx_system_noise_temp_k

            def __process_element(val):
                if isinstance(val, int):
                    return str(val)
                if val > 100:
                    return str(int(val))
                if val > 1000:
                    return '%g'%val
                return '%.2f' % val

            row = [el.gain_db,
                   el.noise_figure_db,
                   el.noise_temp_k,
                   el.prev_gain,
                   el.noise_temp_contrib,
                   el.noise_factor_contrib,
                   ] + [pct*100.0,]
            row = [el.name] + [__process_element(v) for v in row]
            row = (' & '.join(row)) + '\\\\'
            table.append(row)

        table.append('\\end{tabular}')
        return '\n'.join(table)

    def _humanize_hz(self, label, val):
        return (label,) + utils.human_hz(val)

    def _humanize_m(self, label, val):
        return (label,) + utils.human_m(val)

    def _static_pfd_entry(self, bw=0, is_gso=False):
        m = self.model

        if is_gso:
            retval = m.peak_pf_at_geo_dbw_per_m2
        else:
            retval = m.peak_pf_dbw_per_m2

        pfd_per_hz = retval - m.required_bw_dbhz
        if bw:
            retval = pfd_per_hz + min(utils.to_db(bw), m.required_bw_dbhz)
            (bw, bw_unit,) = utils.human_hz(bw)
            if is_gso:
                label = 'Maximum PFD at Geostationary Orbit per %.2g %s' % (bw, bw_unit)
            elif m.is_downlink:
                label = 'Maximum PFD at Earth Surface per %.2g %s' % (bw, bw_unit)
            else:
                label = 'Maximum PFD at Receiver per %.2g %s' % (bw, bw_unit)
            unit = 'dBW/m^2/%.2g%s' % (bw, bw_unit)
        else:
            if is_gso:
                label = 'Peak PFD at GSO'
            else:
                if m.is_downlink:
                    label = 'Peak PFD at Earth Surface'
                else:
                    label = 'Peak PFD at Receiver'
            unit = 'dBW/m^2'
        return (label, retval, unit,)

    def _to_label(self, s):
        return self._file_namify(s)

    def _file_namify(self, s):
        for c in "\"'. \t":
            s = s.replace(c, '_')
        return s

    def to_latex(self,
                 fname,
                 author='',
                 intro='',
                 expo='',
                 rx_pfd_bws=[],
                 gso_pfd_bws=[],
                 pfd_figures=[],
                 added_sections=[],
                 added_interference_sections=[],
                 bitrate_figure=None,
                 watermark_text=None):
        m = self.model
        e = self.model.enum

        if intro is None:
            intro = ''

        top = self._jinja().get_template('budget.tex')

        geometry_items = collections.OrderedDict([
            ('Geometry', [
                ('Altitude of Apogee', m.apogee_altitude_km, 'km'),
                ('Altitude of Perigee', m.perigee_altitude_km, 'km'),
                ('Mean Altitude', m.mean_orbit_altitude_km, 'km'),
                ]),
            ('Constants', [
                ('Earth Radius', m.earth_radius_km, 'km'),
                ('Angle of Elevation from Ground Station', m.min_elevation_deg, '^{\\circ}'),
                ]),
            ('Key Outputs', [
                ('Slant Range at Angle of Elevation', m.slant_range_km, 'km'),
                ('Angle between Satellite Nadir and vector to GS', m.satellite_antenna_angle_deg, '^{\\circ}'),
                ]),
            ])

        tx_items = collections.OrderedDict([
            ('Antenna', [
                ('Gain at Boresight', m.tx_antenna_boresight_gain_dbi, 'dBi'),
                ('Sampled Gain at Angle of Comm Link', m.tx_antenna_gain_dbi, 'dBi'),
                ('Antenna Pointing Loss', m.tx_antenna_pointing_loss_db, 'dB'),
                ('Polarization for Selected Gain Value', m.tx_antenna_polarization, ''),
                ]),

            ('Transmitter', [
                ('Transmit Power at PA', m.tx_power_at_pa_dbw, 'dBW'),
                ('Inline Losses', m.tx_inline_losses_db, 'dB'),
                ('Transmit Power at Antenna', m.tx_power_at_antenna_dbw, 'dBW'),
                ('EIRP', m.tx_eirp_dbw, 'dBW'),
                ]),
            ])

        interference_sections = [
            ('Transmitter', [
                ('Transmit Power at Antenna', m.tx_power_at_antenna_dbw, 'dBW'),
                ('Peak Antenna Gain', m.tx_antenna_peak_gain_dbi, 'dBi'),
                ('Peak EIRP', m.peak_tx_eirp_dbw, 'dBW'),
                ]),
            ]

        pfd_lst = []
        for bw in rx_pfd_bws:
            pfd_lst.append(self._static_pfd_entry(bw=bw, is_gso=False))
        for bw in gso_pfd_bws:
            pfd_lst.append(self._static_pfd_entry(bw=bw, is_gso=True))
        if len(pfd_lst):
            interference_sections.append(('Maximum Power Flux Density at Receiver', pfd_lst))
        interference_sections += added_interference_sections
        
        interference_items = collections.OrderedDict(interference_sections)

        channel_items = collections.OrderedDict([
            ('Constants', [
                self._humanize_hz('Center Frequency', m.center_freq_hz),
                ('Speed of Light', int(m.speed_of_light_m_per_s), 'm/s'),
                ('Wavelength',) + utils.human_m(m.wavelength_m),
                ]),

            ('Losses', [
                ('Unity Gain Propagation Loss (FSPL)', m.unity_gain_propagation_loss_db, 'dB'),
                ('Atmospheric Loss', m.atmospheric_loss_db, 'dB'),
                ('Ionospheric Loss', m.ionospheric_loss_db, 'dB'),
                ('Rain Loss', m.rain_loss_db, 'dB'),
                ('Multipath Fading Loss', m.multipath_fading_db, 'dB'),
                ('Total Channel Loss', m.total_channel_loss_db, 'dB'),
                ]),

            ('Modulation (%s)' % m.modulation_name, [
                self._humanize_hz('Bitrate', m.bitrate_hz),
                ('Bitrate', m.bitrate_dbhz, 'dBHz'),
                self._humanize_hz('Symbol Rate', m.symbol_rate_sym_per_s),
                ('Required Demodulation $E_b/N_0$', m.required_demod_ebn0_db, 'dB'),
                self._humanize_hz('Minimum Required Bandwidth', m.required_bw_hz),
                ('Minimum Required Bandwidth', m.required_bw_dbhz, 'dBHz'),
                ]),
            ])

        rx_items = collections.OrderedDict([
            ('Antenna', [
                ('Gain at Boresight', m.rx_antenna_boresight_gain_dbi, 'dBi'),
                ('Sampled Gain at Angle of Comm Link', m.rx_antenna_gain_dbi, 'dBi'),    
                ('Antenna Pointing Loss', m.rx_antenna_pointing_loss_db, 'dB'),
                ('Antenna Noise Temperature', m.rx_antenna_noise_temp_k, 'K'), 
                ('Polarization for Selected Gain Value', m.rx_antenna_polarization, ''),
                ]),
            ('System', [
                ('Receive Chain Noise Temperature', m.rx_system_noise_temp_k, 'K'),
                ('Receive Chain Noise Factor', m.rx_system_noise_factor, ''),
                ('Receive Chain Noise Figure', m.rx_system_noise_figure, 'dB'),
                ('Total Receiver + Antenna Noise Temperature', m.rx_noise_temp_k, 'K'),
                ('Total Receiver + Antenna Noise Temperature', m.rx_noise_temp_dbk, 'dBK'),
                self._humanize_hz('Receiver Noise Bandwidth', m.rx_noise_bw_hz),
                ('Demod Implementation Loss', m.implementation_loss_db, 'dB'),
                ]),
            ('Cascaded Noise Figure of Receiver', [
                ]),
            ])

        budget_items = collections.OrderedDict([
            ('Transmitter', [
                ('Power at Antenna', m.tx_power_at_antenna_dbw, 'dBW'),
                ('Antenna Gain', m.tx_antenna_gain_dbi, 'dBi'),
                ('Antenna Pointing Loss', m.tx_antenna_pointing_loss_db, 'dB'),
                ('EIRP', m.tx_eirp_dbw, 'dBW'),
                ]),
                
            ('Channel', [
                self._humanize_hz('Center Frequency', m.center_freq_hz),
                ('Unity Gain Propagaion Loss (FSPL)', m.unity_gain_propagation_loss_db, 'dB'),
                ('Total Channel Loss', m.total_channel_loss_db, 'dB'),
                self._humanize_hz('Minimum Required Bandwidth', m.required_bw_hz),
                ]),

            ('Receiver', [
                ('Signal Power Flux at RX Antenna', m.pf_dbw_per_m2, 'dBW/m^2'),
                ('Antenna Gain', m.rx_antenna_gain_dbi, 'dBi'),
                ('Antenna Effective Area', m.rx_antenna_effective_area_dbm2, 'dBmeters'),
                ('Antenna Pointing Loss', m.rx_antenna_pointing_loss_db, 'dB'),
                ('Polarization Mismatch Loss', m.polarization_mismatch_loss_db, 'dB'),
                ('Received Signal Power', m.rx_power_dbw, 'dBW'),
                ('RX System Noise Temperature', m.rx_noise_temp_k, 'K'),
                ('RX Figure of Merit ($G/T$)', m.rx_g_over_t_db, 'dB/K'),
                ('Noise Spectral Density ($N_0$)', m.rx_n0_dbw_per_hz, 'dBW/Hz'),
                ('Excess Noise due to Excess RX BW', m.excess_noise_bandwidth_loss_db, 'dB'),
                ('Demod Implementation Loss', m.implementation_loss_db, 'dB'),
                ('Carrier to Noise Spectral Density($C/N_0$)', m.cn0_db, 'dBHz'),

                ]),

            ('Eb/($N_0$)', [
                ('BitRate', m.bitrate_dbhz, 'dBHz'),
                ('Energy per Bit ($E_b$)', m.rx_eb, 'dBW/Hz'),
                ('Received $E_b/N_0$', m.rx_ebn0_db, 'dB'),
                ('Required $E_b/N_0$ in Ideal RX BW + Demodulator', m.required_demod_ebn0_db, 'dB'),
                ('Required $E_b/N_0$ in this RX BW + Demodulator', m.required_ebn0_db, 'dB'),
                ]),
            ('Key Outputs', [
                ('Link Margin', m.link_margin_db, 'dB'),
                ]),
            ])

        rx_pattern_fname = '%sRXPattern.png' % self._file_namify(m.budget_name)
        m.rx_antenna_obj.plot_pattern(rx_pattern_fname)

        tx_pattern_fname = '%sTXPattern.png' % self._file_namify(m.budget_name)
        m.tx_antenna_obj.plot_pattern(tx_pattern_fname)

        if watermark_text:
            draft_mark = '''
\\newwatermark[allpages,color=black!10,angle=45,scale=3,xpos=0,ypos=0]{%s}
''' % watermark_text
# \\newwatermark[allpages,color=black!10,angle=45,scale=3,xpos=0,ypos=2in]{DRAFT}
        else:
            draft_mark = ''

        if len(expo) > 0:
            expo = '\\newpage\n' + expo

        figs = []
        for fig in pfd_figures:
            fig.plot()
            figs.append(fig.to_latex())
        interference_figures = '\n'.join(figs)

        if bitrate_figure:
            bitrate_figure.plot()
            budget_figures = bitrate_figure.to_latex()
        else:
            budget_figures = ''

        added_tables = []
        for section_name, section in added_sections:
            added_tables.append('''
\\newpage
\\section{%s}
\\label{section::%s}
\\begin{center}
''' % (section_name, self._to_label(section_name)))
            added_tables.append(self._table(collections.OrderedDict(section)))
            added_tables.append('\\end{center}')

        kwargs = {
            'intro':intro,
            'expo':expo,
            'budgetTitle': m.budget_name,
            'table': self._table(budget_items),
            'interferenceFigures': interference_figures,
            'txPatternFname': tx_pattern_fname,
            'rxPatternFname': rx_pattern_fname,
            'draftMark': draft_mark,
            'orbitTable': self._table(geometry_items),
            'transmitterTable': self._table(tx_items),
            'channelTable': self._table(channel_items),
            'receiverTable': self._table(rx_items),
            'rxChainTable': self._rx_chain_table(),
            'interferenceTable': self._table(interference_items),
            'author': author,
            'addedSections': '\n'.join(added_tables),
            'budgetFigures': budget_figures,
            }
        with open(fname, 'w') as fd:
            fd.write(top.render(**kwargs))

    def _jinja(self, basedir='/usr/local/share/pylink'):
        env = jinja2.Environment(
            block_start_string = '\BLOCK{',
            block_end_string = '}',
            variable_start_string = '\VAR{',
            variable_end_string = '}',
            comment_start_string = '\#{',
            comment_end_string = '}',
            line_statement_prefix = '%%',
            line_comment_prefix = '%#',
            trim_blocks = True,
            autoescape = False,
            loader = jinja2.FileSystemLoader(basedir))
        return env
