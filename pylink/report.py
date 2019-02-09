#!/usr/bin/python

import collections
import distutils.sysconfig
import jinja2
import matplotlib.pyplot as plt
import numpy as np
import os
import site

import pylink.utils as utils


class Figure(object):

    def __init__(self, title=None):
        self.title = title

    def to_latex(self, dname='.', fname=None):

        if not fname:
            fname = self.fname()

        # LaTeX does NOT play nicely with backslashes in windows
        path = os.path.join(dname, fname).replace('\\', '/')

        return '''
  \\begin{figure}
    \\caption{%s}
    \\includegraphics[width=\\linewidth]{%s}
    \\label{fig::pfd::%s}
  \\end{figure}
        ''' % (self.caption(), path, self.label())

    def _plot_vs_el(self, y_func, dname='.', fname=None):
        m = self.model
        e = self.model.enum

        orig_el = m.override_value(e.min_elevation_deg)

        fig = plt.figure()
        if self.title:
            fig.suptitle(self.title)
        ax = fig.add_subplot(1, 1, 1)

        # Plot any limit lines
        if 'pfd_limits' in vars(self) and self.pfd_limits:
            x = [p[0] for p in self.pfd_limits]
            y = [p[1] for p in self.pfd_limits]
            ax.plot(x, y, color='r', linewidth=2, label='Limit')

        # Now plot the PFD curve
        x = np.linspace(0.0, 90.0, 90)
        y = np.linspace(0.0, 90.0, 90)

        for i in range(len(x)):
            m.override(e.min_elevation_deg, x[i])
            y[i] = y_func(i)

        ax.plot(x, y, color='b')
        ax.set_xlabel('Elevation Angle (degrees)')
        ax.set_ylabel(self.ylabel())

        # XXX: matplotlib is doing weird things if you set ylim this way
        # if 'pfd_limits' in vars(self) and self.pfd_limits:
        #     upper = max(max(y), self.pfd_limits[-1][1])
        #     lower = min(min(y), self.pfd_limits[0][1])

        #     delta = upper - lower
        #     upper += delta*0.1
        #     lower -= delta*0.1

        #     plt.ylim(lower, upper)
        # else:
        #     upper = max(y)
        #     lower = min(y)

        if not fname:
            fname = self.fname()
        path = os.path.join(dname, fname)
        fig.savefig(path, transparent=True)

        if orig_el is not None:
            m.override(e.min_elevation_deg, orig_el)
        else:
            m.reset(e.min_elevation_deg)


class CanonicalPFDFigure(Figure):
    """Power Flux Density figure for the canonical PFD vs Elevation

    The canonical figure assumes complete and even use of the
    spectrum, and it also tends to assume max eirp from the
    transmitter.  Becauses this model is really only used for
    compliance purposes, we ignore things like rain losses.

    This figure also assumes we are dealing with a space-to-earth
    link.  For NGSO to GSO, or earth-to-space, this figure is
    inapplicable.

     * Space-to-Earth
     * Boresight
     * Full BW Utilization
    """

    def __init__(self,
                 model,
                 bw=4e3,
                 pfd_limits=None,
                 title=None):
        """Creates a new canonical pfd figure.

        model -- The DAG model.
        bw -- BW for the PFD (defaults to 4kHz
        pfd_limits -- If it is PFD vs elevation, also plot these PFD limits
        """
        self.title = title
        self.model = model
        self.pfd_limits = pfd_limits
        self.bw = bw

    def label(self):
        return 'pfd-canonical-%d%s' % utils.human_hz(self.bw)

    def fname(self):
        return 'pfd-canonical-%d%s.png' % utils.human_hz(self.bw)

    def ylabel(self):
        return 'Boresight PFD (dBW/m^2/%d%s)' % utils.human_hz(self.bw)

    def caption(self):
        return "Peak PFD at Earth Station assuming full BW utilization"

    def plot(self, dname='.', fname=None):
        def __y(i):
            m = self.model
            return utils.pfd_hz_manual_adjust(m.canonical_pf_dbw_per_m2,
                                              m.allocation_hz,
                                              self.bw)
        return self._plot_vs_el(__y, dname=dname, fname=fname)


class ExpectedPFDFigure(Figure):
    """Power Flux Density figure for the expected case

    The expected case is much more complicated and includes things
    like antenna patterns, satellite pointing, and modulation code
    selection.  Typically, when a higher modulation code is selected,
    the BW utilization drops slightly resulting in slightly higher PFD
    because the total signal power is spread over slightly fewer Hz.
    As a result, this graph is not expected to be smooth.  It should,
    however, be monotonic.

    This figure also assumes we are dealing with a space-to-earth
    link.  For NGSO to GSO, or earth-to-space, this figure is
    inapplicable.

     * Space-to-Earth
     * Expected antenna gain
     * Expected BW utilization
    """

    def __init__(self,
                 model,
                 bw=4e3,
                 pfd_limits=None,
                 title=None):
        """Creates a new canonical pfd figure.

        model -- The DAG model.
        bw -- BW for the PFD (defaults to 4kHz
        pfd_limits -- If it is PFD vs elevation, also plot these PFD limits
        """
        self.title = title
        self.model = model
        self.pfd_limits = pfd_limits
        self.bw = bw

    def label(self):
        return 'pfd-expected-%d%s' % utils.human_hz(self.bw)

    def ylabel(self):
        return 'Expected PFD (dBW/m^2/%d%s)' % utils.human_hz(self.bw)

    def fname(self):
        return 'pfd-expected-%d%s.png' % utils.human_hz(self.bw)

    def caption(self):
        return "Expected PFD at Earth Station under normal operations"

    def plot(self, dname='.', fname=None):
        def __y(i):
            return utils.rx_pfd_hz_adjust(self.model,
                                          self.model.pf_dbw_per_m2,
                                          self.bw)
        return self._plot_vs_el(__y, dname=dname, fname=fname)


class PFDvsBWFigure(Figure):
    """Peak Power Flux Density figure vs BandWidth

    For compliance reasons, it can be useful to show a graph of the
    peak acheivable PFD vs BW for both the receiver and the GSO case.

     * Space-to-Earth or Earth-to-Space
     * Peak antenna gain
     * Full BW utilization
     * GSO or Receiver
    """

    def __init__(self,
                 model,
                 start_hz=1,
                 end_hz=4e3,
                 is_gso=False,
                 pfd_limits=None,
                 title=None):
        """Creates a new figure.

        model -- The DAG model.
        start_hz -- If so, starting BW
        end_hz -- And the ending BW
        is_gso -- True if looking at PFD at GSO, otherwise it is the receiver
        pfd_limits -- plot these PFD limits
        """

        self.title = title
        self.model = model
        self.start_hz = start_hz
        self.end_hz = end_hz
        self.is_gso = is_gso
        self.pfd_limits = pfd_limits

    def fname(self):
        prefix = 'gso' if self.is_gso else 'rx'
        prefix = 'pfd-' + prefix
        return '%s_%d-%d.png' % (prefix, self.start_hz, self.end_hz)

    def label(self):
        prefix = 'gso' if self.is_gso else 'rx'
        return '%s_%d-%d' % (prefix, self.start_hz, self.end_hz)

    def caption(self):
        if self.is_gso:
            return 'Peak PFD at GSO vs Bandwidth'
        else:
            if self.model.is_downlink:
                return 'Peak PFD at Surface vs Bandwidth'
            else:
                return 'Peak PFD at Receiver vs Bandwidth'

    def plot(self, dname='.', fname=None):
        m = self.model

        if self.is_gso:
            pf = m.peak_pf_at_geo_dbw_per_m2
        else:
            pf = m.peak_pf_dbw_per_m2

        fig = plt.figure()
        if self.title:
            fig.suptitle(self.title)
        ax = fig.add_subplot(1, 1, 1)
        n = int(self.end_hz) - int(self.start_hz)
        x = np.linspace(1, n, n-1)
        x += self.start_hz
        y = np.zeros(n-1)
        for i in range(len(x)):
            bw = x[i]
            y[i] = utils.pfd_hz_manual_adjust(pf, m.allocation_hz, bw)

        ax.plot(x, y, color='b', label='PFD (dBW/m^2)')

        # Plot any limit lines
        if self.pfd_limits:
            x = [p[0] for p in self.pfd_limits]
            y = [p[1] for p in self.pfd_limits]
            ax.plot(x, y, color='r', linewidth=2, label='Limit')


        ax.set_xlabel('Bandwidth (Hz)')
        if self.is_gso:
            ax.set_ylabel('PFD at GSO(dBW/m^2)')
        else:
            ax.set_ylabel('PFD at Receiver (dBW/m^2)')
        if not fname:
            fname = self.fname()
        path = os.path.join(dname, fname)
        fig.savefig(path, transparent=True)


class BitrateFigure(Figure):
    """Max bitrate vs Elevation Figure

    This graph assumes normal operations and indicates the max
    available bitrate.
    """

    def __init__(self, model, title):
        self.model = model
        self.title = title

    def label(self):
        return 'max-bitrate'

    def fname(self):
        return 'max-bitrate.png'

    def caption(self):
        return 'Bitrate with %ddB of Link Margin vs Elevation' % self.model.target_margin_db

    def ylabel(self):
        return 'Max Bitrate (MHz)'

    def plot(self, dname='.', fname=None):
        def __y(i):
            R = self.model.max_bitrate_hz
            m = self.model
            return self.model.max_bitrate_hz / 1.0e6
        return self._plot_vs_el(__y, dname=dname, fname=fname)


class Report(object):
    """LaTeX report Generator.

    Generates latex reports with great extensibility for either
    general engineering, or compliance reports for people like
    NOAA/NASA/FCC/ITU/ESA/TLA/ETLA.
    """

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
                  ('Gain', 'dB', .47),
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

        pfd_per_hz = retval - m.required_rx_bw_dbhz
        if bw:
            retval = pfd_per_hz + min(utils.to_db(bw), m.required_rx_bw_dbhz)
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
        """Export the budget to LaTeX

        fname -- Top level latex path
        author -- The author's name/entry in the header
        intro -- An optional section of latex to be included after the title
        expo -- An optional section of latex to be included at the end
        rx_pfd_bws -- List of PFD BW's to include in the interference section
        gso_pfd_bws -- List of PFD BW's to include in the interference section
        added_sections -- Additional sections to add before the budget section
        added_iterference_sections -- Additional subsections for interference
        pfd_figures -- Any desired PFD figure objects
        bitrate_figure -- Any desired bitrate figure objects
        watermark_text -- Watermark text (such as DRAFT or CONFIDENTIAL)

        Interference Subsections:
        [('Subsection Title', [
            ('Item Name', item_value, 'units'),
            ('Another Item Name', another_value, 'units'),
          ]),]

        Additional Sections:
        [('Section Name', [
            subsection,
            subsection,
          ]),]
        """
        
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
                ('Total Channel Loss', m.total_channel_loss_db, 'dB'),
                ]),

            ('Modulation (%s)' % m.modulation_name, [
                ('Modulation Name', m.modulation_name, ''),
                ('Modulation Code', m.best_modulation_code.name, ''),
                ('Tx Spectral Efficiency', m.best_modulation_code.tx_eff, ''),
                self._humanize_hz('Bitrate', m.bitrate_hz),
                ('Bitrate', m.bitrate_dbhz, 'dBHz'),
                ('Required Demodulation $E_b/N_0$', m.required_demod_ebn0_db, 'dB'),
                self._humanize_hz('Required Demod Bandwidth', m.required_rx_bw_hz),
                ('Required Demod Bandwidth', m.required_rx_bw_dbhz, 'dBHz'),
                ('Required Transmit Bandwidth', m.required_tx_bw_dbhz, 'dBHz'),
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
                ('Occupied Bandwidth', m.required_tx_bw_dbhz, 'dBHz'),
                ]),

            ('Receiver', [
                ('Signal Power Flux at RX Antenna', m.pf_dbw_per_m2, 'dBW/m^2'),
                ('Antenna Gain', m.rx_antenna_gain_dbi, 'dBi'),
                ('Antenna Effective Area', m.rx_antenna_effective_area_dbm2, 'dBm^2'),
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
                self._humanize_hz('Bitrate', m.bitrate_hz),
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
            fig.plot(dname=os.path.dirname(fname))
            figs.append(fig.to_latex())
        interference_figures = '\n'.join(figs)

        if bitrate_figure:
            bitrate_figure.plot(dname=os.path.dirname(fname))
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


    def _jinja(self, basedir=None):
        if not basedir:
            lib = distutils.sysconfig.get_python_lib()
            rel = 'pylink/tex'
            basedir = os.path.join(lib, rel)

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
