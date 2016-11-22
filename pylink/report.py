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
        ax.set_xlabel('Elevation Angle (degrees)')
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
            retval = '%s_%d-%d.png' % (prefix, self.start_hz, self.end_hz)
        else:
            retval = 'rx-vsEl.png'
        return os.path.join(self.dname, retval)

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
                 dname='.',
                 is_bw=True,
                 start_hz=0,
                 bw=4e3,
                 end_hz=4e3,
                 is_gso=False,
                 pfd_limits=None):
        self.dname = dname
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
        start_pfd = m.pf_dbw_per_m2

        min_angle = 0
        min_pfd = m.pf_dbw_per_m2
        min_bitrate = m.bitrate_dbhz

        max_angle = 0
        max_pfd = m.pf_dbw_per_m2
        max_bitrate = m.bitrate_dbhz

        for i in range(91):
            m.override(e.min_elevation_deg, i)
            pfd = m.pf_dbw_per_m2
            pfd_delta = pfd - start_pfd
            bitrate = start_bitrate + pfd_delta

            if min_pfd > pfd:
                min_pfd = pfd
                min_angle = i
                min_bitrate = bitrate

            if max_pfd < pfd:
                max_pfd = pfd
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
        fig.savefig(self.fname())

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


class Report(object):

    def __init__(self, model):
        self.model = model
        self.enum = model.enum

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
                  #('Gain Factor', '', .5),
                  #('Noise Factor', '', .5),
                  ('Noise Temp.', 'K', .5),
                  ('Upstream Gain Factor', '', .6),
                  ('Contrib. Noise Temp', 'K', .5),
                  ('Contrib. Noise Factor', '', .5),
                  ('Noise Temp Pct Contrib.', '\\%', .75),
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
                label = 'Peak PFD at GSO per %.2g%s' % (bw, bw_unit)
            elif m.is_downlink:
                label = 'Peak PFD at Surface per %.2g%s' % (bw, bw_unit)
            else:
                label = 'Peak PFD at Receiver per %.2g%s' % (bw, bw_unit)
            unit = 'dBW/m^2/%.2g%s' % (bw, bw_unit)
        else:
            if is_gso:
                label = 'Peak PFD at GSO'
            else:
                if m.is_downlink:
                    label = 'Peak PFD at Surface'
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

        dname = os.path.dirname(fname)

        if intro is None:
            intro = ''

        top = self._jinja().get_template('budget.tex')

        orbit_items = collections.OrderedDict([
            ('Orbit', [
                ('Apoapsis', m.apoapsis_altitude_km, 'km'),
                ('Periapsis', m.periapsis_altitude_km, 'km'),
                ('Mean Altitude', m.mean_orbit_altitude_km, 'km'),
                ]),
            ('Constants', [
                ('Earth Radius', m.earth_radius_km, 'km'),
                ('GS Angle of Elevation', m.min_elevation_deg, '^{\\circ}'),
                ]),
            ('Key Outputs', [
                ('Slant Range', m.slant_range_km, 'km'),
                ('Satellite Angle from Boresight', m.satellite_antenna_angle_deg, '^{\\circ}'),
                ]),
            ])

        tx_items = collections.OrderedDict([
            ('Antenna', [
                ('Sampled Gain', m.tx_antenna_gain_dbi, 'dBi'),
                ('Antenna Pointing Loss', m.tx_antenna_pointing_loss_db, 'dB'),
                ('Gain at Boresight', m.tx_antenna_boresight_gain_dbi, 'dBi'),
                ('Average Nadir Gain', m.tx_antenna_average_nadir_gain_dbi, 'dBi'),
                ('Polarization', m.tx_antenna_polarization, ''),
                ]),

            ('Transmitter', [
                ('Transmit Power at PA', m.tx_power_at_pa_dbw, 'dBW'),
                ('Inline Losses', m.tx_inline_losses_db, 'dB'),
                ('Transmit Power at Antenna', m.tx_power_at_antenna_dbw, 'dBW'),
                ('EIRP', m.tx_eirp_dbw, 'dBW'),
                # EVM
                ]),
            ])

        interference_sections = [
            ('Transmitter', [
                ('Transmit Power at Antenna', m.tx_power_at_antenna_dbw, 'dBW'),
                ('Peak Antenna Gain', m.tx_antenna_peak_gain_dbi, 'dBi'),
                ('Peak EIRP', m.peak_tx_eirp_dbw, 'dBW'),
                ('Nadir-to-GS Gain', m.tx_antenna_gain_dbi, 'dBi'),
                ('Nadir-to-GS EIRP', m.tx_eirp_dbw, 'dBW'),
                ('Average Antenna Gain', m.tx_antenna_average_gain_dbi, 'dBi'),
                ]),
            ]

        pfd_lst = []
        for bw in rx_pfd_bws:
            pfd_lst.append(self._static_pfd_entry(bw=bw, is_gso=False))
        for bw in gso_pfd_bws:
            pfd_lst.append(self._static_pfd_entry(bw=bw, is_gso=True))
        if len(pfd_lst):
            interference_sections.append(('Peak Power Flux Density at Receiver', pfd_lst))
        interference_sections += added_interference_sections

        interference_items = collections.OrderedDict(interference_sections)

        channel_items = collections.OrderedDict([
            ('Constants', [
                self._humanize_hz('Center Frequency', m.center_freq_hz),
                ('Speed of Light', int(m.speed_of_light_m_per_s), 'm/s'),
                self._humanize_hz('Allocated Bandwidth', m.allocation_hz),
                self._humanize_hz('Start of Allocation', m.allocation_start_hz),
                self._humanize_hz('End of Allocation', m.allocation_end_hz),
                ('Wavelength',) + utils.human_m(m.wavelength_m),
                ]),

            ('Losses', [
                ('Unity Gain Propagation Loss', m.unity_gain_propagation_loss_db, 'dB'),
                ('Atmospheric Loss', m.atmospheric_loss_db, 'dB'),
                ('Ionospheric Loss', m.ionospheric_loss_db, 'dB'),
                ('Rain Loss', m.rain_loss_db, 'dB'),
                ('Multipath Fading Loss', m.multipath_fading_db, 'dB'),
                ('Polarization Mismatch Loss', m.polarization_mismatch_loss_db, 'dB'),
                ('Total Channel Loss', m.total_channel_loss_db, 'dB'),
                ]),

            ('Modulation (%s)' % m.modulation_name, [
                self._humanize_hz('Bitrate', m.bitrate_hz),
                ('Bitrate', m.bitrate_dbhz, 'dBHz'),
                self._humanize_hz('Symbol Rate', m.symbol_rate_sym_per_s),
                ('Required Demodulation $E_b/N_0$', m.required_demod_ebn0_db, 'dB'),
                self._humanize_hz('Required Bandwidth', m.required_bw_hz),
                ('Required Bandwidth', m.required_bw_dbhz, 'dBHz'),
                ]),
            ])

        rx_items = collections.OrderedDict([
            ('Antenna', [
                ('Noise Temperature', m.rx_antenna_noise_temp_k, 'K'),
                ('Sampled Gain', m.rx_antenna_gain_dbi, 'dBi'),
                ('Antenna Pointing Loss', m.rx_antenna_pointing_loss_db, 'dB'),
                ('Gain at Boresight', m.rx_antenna_boresight_gain_dbi, 'dBi'),
                ('Average Nadir Gain', m.rx_antenna_average_nadir_gain_dbi, 'dBi'),
                ('Polarization', m.rx_antenna_polarization, ''),
                ]),

            ('System', [
                ('Total Receiver Noise Temperature', m.rx_noise_temp_k, 'K'),
                ('Total Receiver Noise Temperature', m.rx_noise_temp_dbk, 'dBK'),
                ('Receive Chain Noise Temperature', m.rx_system_noise_temp_k, 'K'),
                ('Receive Chain Noise Factor', m.rx_system_noise_factor, ''),
                ('Receive Chain Noise Figure', m.rx_system_noise_figure, 'dB'),
                self._humanize_hz('Receiver Noise Bandwidth', m.bitrate_hz),
                ('Implementation Loss', m.implementation_loss_db, 'dB'),
                ]),
            ])

        budget_items = collections.OrderedDict([
            ('Transmitter', [
                ('Power at Antenna', m.tx_power_at_antenna_dbw, 'dBW'),
                ('Gain', m.tx_antenna_gain_dbi, 'dBi'),
                ('Antenna Pointing Loss', m.tx_antenna_pointing_loss_db, 'dB'),
                ('EIRP', m.tx_eirp_dbw, 'dBW'),
                ]),
                
            ('Channel', [
                self._humanize_hz('Center Frequency', m.center_freq_hz),
                ('Free Space Loss', m.unity_gain_propagation_loss_db, 'dB'),
                ('Total Channel Loss', m.total_channel_loss_db, 'dB'),
                ('Occupied Bandwidth', m.required_bw_dbhz, 'dBHz'),
                ]),

            ('Receiver', [
                ('Signal Power Flux at RX Antenna', m.pf_dbw_per_m2, 'dBW/m^2'),
                ('Antenna Gain', m.rx_antenna_gain_dbi, 'dBi'),
                ('Antenna Effective Area', m.rx_antenna_effective_area_dbm2, 'dBm'),
                ('Polarization Mismatch Loss', m.polarization_mismatch_loss_db, 'dB'),
                ('RX System Noise Temperature', m.rx_noise_temp_k, 'K'),
                ('RX Figure of Merit ($G/T$)', m.rx_g_over_t_db, 'dB/K'),
                ('Noise Spectral Density ($N_0$)', m.rx_n0_dbw_per_hz, 'dBW/Hz'),
                ('Received Signal Power', m.rx_power_dbw, 'dBW'),
                ('Excess Noise BW Loss', m.excess_noise_bandwidth_loss_db, 'dB'),
                ('Implementation Loss', m.implementation_loss_db, 'dB'),
                ('Required Demodulation $E_b/N_0$', m.required_demod_ebn0_db, 'dB'),
                ('Antenna Pointing Loss', m.rx_antenna_pointing_loss_db, 'dB'),
                ('Carrier to Noise ($C/N_0$)', m.cn0_db, 'dBHz'),

                ]),

            ('Eb/N0', [
                ('BitRate', m.bitrate_dbhz, 'dBHz'),
                ('Energy per Bit ($E_b$)', m.rx_eb, 'dBW/Hz'),
                ('Received $E_b/N_0$', m.rx_ebn0_db, 'dB'),
                ('Required $E_b/N_0$', m.required_ebn0_db, 'dB'),
                ]),
            ('Key Outputs', [
                ('Link Margin', m.link_margin_db, 'dB'),
                ]),
            ])

        rx_pattern_fname = '%sRXPattern.png' % self._file_namify(m.budget_name)
        m.rx_antenna_obj.plot_pattern(os.path.join(dname, rx_pattern_fname))

        tx_pattern_fname = '%sTXPattern.png' % self._file_namify(m.budget_name)
        m.tx_antenna_obj.plot_pattern(os.path.join(dname, tx_pattern_fname))

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
            'orbitTable': self._table(orbit_items),
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
