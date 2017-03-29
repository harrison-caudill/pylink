#!/usr/bin/python

import os
import shutil
import subprocess
import sys
import pylink
import numpy as np

###############################################################################
# Intro                                                                       #
###############################################################################

intro = """
Example link budget for downlink where satellite uses fixed gain value
and ground station uses antenna pattern.
"""
# Name for report file generation
link_name = "sdown_gs_antpat"
output_fname = "sd"

# set is_downlink=False for uplink
is_downlink = True

###############################################################################
# Geometry                                                                    #
###############################################################################
geometry = pylink.Geometry(apogee_altitude_km=650,
                           perigee_altitude_km=650,
                           min_elevation_deg=10)

###############################################################################
# Transmitter                                                                 #
###############################################################################

# Candidate amplifier
gs_transmitter = pylink.Transmitter(tx_power_at_pa_dbw=1.25,
                                    name='Satellite')

# Current modulation
modulation = pylink.Modulation(name='QPSK',
                               required_ebn0_db=5.5,
                               bits_per_symbol=2,
                               spectral_efficiency_bps_per_hz=2)

tx_con_chain = [
    pylink.Element(name='Coax Interconnect',
                   gain_db=-0.5,
                   noise_figure_db=0.5), ]
tx_interconnect = pylink.Interconnect(rf_chain=tx_con_chain, is_rx=False)

# Antenna gain value was taken from example antenna similar to what PL uses
tx_antenna = pylink.Antenna(gain=0,
                            polarization='RHCP',
                            pointing_loss_db=0,
                            is_rx=False,
                            tracking=False)

###############################################################################
# Channel                                                                     #
###############################################################################

# Assumes 0 losses to make the compliance pfd and the regular pfd the same
channel = pylink.Channel(bitrate_hz=250e3,
                         allocation_hz=5e6,
                         center_freq_mhz=2022.5,
                         atmospheric_loss_db=0,
                         ionospheric_loss_db=0,
                         rain_loss_db=0,
                         multipath_fading_db=0,
                         polarization_mismatch_loss_db=0)


###############################################################################
# Receiver                                                                    #
###############################################################################
# Import 2D antenna pattern data from measurement data file from ARA
pat_fname = '../antenna_patterns/pattern_sband_gs_phi0.txt'

# Column index of angles in 2D pattern cut
pat_col_theta = 0

# Column index of angle to select cut from 3D data
pat_col_phi = None

# Column index of gain values to use in cut
pat_col_gain = 1

# Number of header rows in data file to skip
pat_nrows_skipheader = 9

# Delimiter to parse file. If "None", loadtxt will use whitespace as default
pat_delimiter = None

# Calibrated max gain value to shift entire pattern.  Often, measured antenna
# data is recorded in dB relative to reference value other than dBi.  Then the
# data is accompanied by a report with the actual gain in dBi of main lobe.
pat_maxgain_set_dbi = 25.7

# Rotation angle by which to rotate the pattern data.  Sometimes measurement
# data has an angle offset due to test fixtures such that boresight is not at 0
# Observe pattern data first and apply this offset to rotate as needed.
pat_rotate_deg = 2

# Angle step size on wihch to interpolate raw data from antenna pattern file.
# Often, antenna pattern measurement data files are not uniform due to
# mechanics of measurments system.  Or simulation / measurement data is sparse.
pat_interp_angle_step_deg = 0.5

# Set override for pattern plot display range minimum and maximum gain values
# If this value is not passed into Antenna object instantiation, it will be
# it will be calculated automatically.
pat_plot_ylim = (-10, 30)

# Set override for pattern plot display gain step size.
# # If this value is not passed into Antenna object instantiation, it will be
# the default value of 5 will be used
pat_plot_ystep = 5

angles_theta_deg, gain_dB = np.loadtxt(pat_fname,
                                       usecols=(pat_col_theta, pat_col_gain),
                                       delimiter=pat_delimiter,
                                       unpack=True,
                                       skiprows=pat_nrows_skipheader)

gain_cut_dB = gain_dB
angles_theta_cut_deg = angles_theta_deg

# Example with antenna pattern data available
rx_antenna = pylink.Antenna(pattern_gain_db=gain_cut_dB,
                            pattern_angles_deg=angles_theta_deg,
                            pattern_maxgain_set_dbi=pat_maxgain_set_dbi,
                            pattern_rotate_deg=pat_rotate_deg,
                            pattern_interp_angle_step_deg=pat_interp_angle_step_deg,
                            polarization='RHCP',
                            pointing_loss_db=0,
                            is_rx=True,
                            tracking=True,
                            noise_temp_k=100)

# Example with manual antenna gain data entry, fixed value
# rx_antenna = pylink.Antenna(gain=25.7,
#                             polarization='RHCP',
#                             pointing_loss_db=0,
#                             is_rx=True,
#                             noise_temp_k=100,
#                             tracking=True)

rx_con_chain = [pylink.Element(name='N conn',
                               gain_db=-0.05,
                               noise_figure_db=0.05), ]
rx_interconnect = pylink.Interconnect(rf_chain=rx_con_chain, is_rx=True)

rx_rf_chain = [pylink.Element(name='LNA',
                              gain_db=32,
                              noise_figure_db=0.4),
               pylink.Element(name='20 ft. LMR-400 UF',
                              gain_db=-1.7,
                              noise_figure_db=1.7),
               pylink.Element(name='LPU',
                              gain_db=-0.2,
                              noise_figure_db=0.2),
               pylink.Element(name='100 ft. LMR-600',
                              gain_db=-4.4,
                              noise_figure_db=4.4),
               pylink.Element(name='Bias Tee',
                              gain_db=-1,
                              noise_figure_db=1),
               pylink.Element(name='Adapter N-SMA',
                              gain_db=-0.1,
                              noise_figure_db=0.1),
               pylink.Element(name='SAW BPF',
                              gain_db=-2,
                              noise_figure_db=2),
               pylink.Element(name='1 ft. Flex 141',
                              gain_db=-0.2,
                              noise_figure_db=0.2),
               pylink.Element(name='USRP+SBX rxg 20',
                              gain_db=20,
                              noise_figure_db=15), ]
receiver = pylink.Receiver(rf_chain=rx_rf_chain,
                           implementation_loss_db=2,
                           noise_bw_khz=250,
                           name='Ground Station')

###############################################################################
# Budgets                                                                     #
###############################################################################
extras = {}
link = pylink.LinkBudget(defaults=[geometry,
                                   gs_transmitter,
                                   modulation,
                                   tx_interconnect,
                                   tx_antenna,
                                   channel,
                                   rx_antenna,
                                   rx_interconnect,
                                   receiver, ],
                         name=link_name,
                         is_downlink=is_downlink,
                         **extras)

###############################################################################
# Transmitted Interference Analysis                                           #
###############################################################################
rx_pfd_bws = [1, 4000]
gso_pfd_bws = [1, 4000]
pfd_fig1 = pylink.PFDFigure(link,
                            is_bw=False,
                            start_hz=0,
                            bw=4e3,
                            end_hz=4e3,
                            is_gso=False,
                            pfd_limits=None)
pfd_figs = [pfd_fig1]

###############################################################################
# Utility Functions                                                           #
###############################################################################


def export(b,
           prefix,
           refresh=False,
           intro='',
           expo='',
           added_sections=[],
           added_interference_sections=[],
           rx_pfd_bws=[],
           gso_pfd_bws=[],
           pfd_figures=[]):

    start_dir = os.getcwd()
    dname = os.path.join('export', b.model.budget_name.replace(' ', ''))
    if refresh:
        if not os.path.exists(dname):
            os.makedirs(dname)
    else:
        if os.path.exists(dname):
            shutil.rmtree(dname)
        os.makedirs(dname)

    os.chdir(dname)
    tname = '%s.tex' % prefix
    author = ''
    # author = 'Spiro Sarris \\textless spiro.sarris@spire.com\\textgreater'
    b.to_latex(tname,
               author,
               intro=intro,
               expo=expo,
               added_sections=added_sections,
               rx_pfd_bws=rx_pfd_bws,
               gso_pfd_bws=gso_pfd_bws,
               pfd_figures=pfd_figures)
    if not refresh:
        subprocess.call(['pdflatex', tname])
    subprocess.call(['pdflatex', tname])
    os.chdir(start_dir)

###############################################################################
# Main                                                                        #
###############################################################################


if __name__ == '__main__':
    m = link.model
    export(link, output_fname,
           refresh=('r' in ''.join(sys.argv)),
           intro=intro,
           rx_pfd_bws=rx_pfd_bws,
           gso_pfd_bws=gso_pfd_bws,
           pfd_figures=pfd_figs
           )
