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
Example link budget for downlink where satellite uses antenna pattern and 
and ground station uses fixed gain value
"""
# Name for report file generation
link_name = "xdown_sat_antpat"
output_fname = "xd"

# set is_downlink=False for uplink
is_downlink = True

###############################################################################
# Geometry                                                                    #
###############################################################################

geometry = pylink.Geometry(apogee_altitude_km=650,
                           perigee_altitude_km=650,
                           min_elevation_deg=60)

###############################################################################
# Transmitter                                                                 #
###############################################################################

# Candidate amplifier
gs_transmitter = pylink.Transmitter(tx_power_at_pa_dbw=3,
                                    name='Satellite')

# Current modulation
modulation = pylink.Modulation(name='DVB-S2X 8PSK',
                               required_ebn0_db=6.5,
                               bits_per_symbol=2,
                               spectral_efficiency_bps_per_hz=3)

tx_con_chain = [
    pylink.Element(name='Coax Interconnect',
                   gain_db=-0.5,
                   noise_figure_db=0.5), ]
tx_interconnect = pylink.Interconnect(rf_chain=tx_con_chain, is_rx=False)

# Import 3D antenna pattern data from file in GDrive Comms Simulation X-band
pat_fname = '../antenna_patterns/patch_uni_array_rlzGain.txt'

# Column index of angles in 2D pattern cut
pat_col_theta = 0

# Column index of angle to select cut from 3D data
pat_col_phi = 1

# Column index of gain values to use in cut
pat_col_gain = 5

# Number of header rows in data file to skip
pat_nrows_skipheader = 2

# Delimiter to parse file. If "None", loadtxt will use whitespace as default
pat_delimiter = None

# Calibrated max gain value to shift entire pattern.  Often, measured antenna
# data is recorded in dB relative to reference value other than dBi.  Then the
# data is accompanied by a report with the actual gain in dBi of main lobe.
pat_maxgain_set_dbi = None

# Rotation angle by which to rotate the pattern data.  Sometimes measurement
# data has an angle offset due to test fixtures such that boresight is not at 0
# Observe pattern data first and apply this offset to rotate as needed.
pat_rotate_deg = 0

# Angle step size on wihch to interpolate raw data from antenna pattern file.
# Often, antenna pattern measurement data files are not uniform due to
# mechanics of measurments system.  Or simulation / measurement data is sparse.
pat_interp_angle_step_deg = 1

# Set override for pattern plot display range minimum and maximum gain values
# If this value is not passed into Antenna object instantiation, it will be
# it will be calculated automatically.
pat_plot_ylim = (-10, 20)

# Set override for pattern plot display gain step size.
# # If this value is not passed into Antenna object instantiation, it will be
# the default value of 5 will be used
pat_plot_ystep = 5

angles_theta_deg, angles_phi_deg, gain_dBi = np.loadtxt(
    pat_fname,
    usecols=(pat_col_theta, pat_col_phi, pat_col_gain),
    delimiter=pat_delimiter,
    unpack=True,
    skiprows=pat_nrows_skipheader)

# Choose phi angle to define 2D cut of 3D pattern
pat_phi_select_deg = 0
i_phi_select = np.where(angles_phi_deg == pat_phi_select_deg)

gain_cut_dBi = gain_dBi[i_phi_select]
angles_theta_cut_deg = angles_theta_deg[i_phi_select]

# Example with antenna pattern data available
tx_antenna = pylink.Antenna(pattern_gain_db=gain_cut_dBi,
                            pattern_angles_deg=angles_theta_cut_deg,
                            pattern_maxgain_set_dbi=pat_maxgain_set_dbi,
                            pattern_rotate_deg=pat_rotate_deg,
                            pattern_interp_angle_step_deg=pat_interp_angle_step_deg,
                            polarization='RHCP',
                            pointing_loss_db=0,
                            is_rx=False,
                            tracking=False)

# Example with manual antenna gain data entry, no pattern
# tx_antenna = pylink.Antenna(gain=14,
#                             polarization='RHCP',
#                             pointing_loss_db=0,
#                             is_rx=False,
#                             tracking=False)


###############################################################################
# Channel                                                                     #
###############################################################################

# Assumes 0 losses to make the compliance pfd and the regular pfd the same
channel = pylink.Channel(bitrate_hz=60e6,
                         allocation_hz=60e6,
                         center_freq_mhz=8212.5,
                         atmospheric_loss_db=0,
                         ionospheric_loss_db=0,
                         rain_loss_db=0,
                         multipath_fading_db=0,
                         polarization_mismatch_loss_db=0)


###############################################################################
# Receiver                                                                    #
###############################################################################

rx_antenna = pylink.Antenna(gain=44.8,
                            polarization='RHCP',
                            pointing_loss_db=0,
                            is_rx=True,
                            noise_temp_k=0,
                            tracking=True)

# Antenna noise temp = 0 here because Orbital rolls this into G/T for total
# Antenna + RX system and it is included as noise_figure_db in rx_con_chain

rx_con_chain = [pylink.Element(name='Orbital RX',
                               gain_db=0,
                               noise_figure_db=1.95), ]
rx_interconnect = pylink.Interconnect(rf_chain=rx_con_chain, is_rx=True)

rx_rf_chain = [pylink.Element(name='USRP+UBX rxg 20',
                              gain_db=20,
                              noise_figure_db=0), ]
receiver = pylink.Receiver(rf_chain=rx_rf_chain,
                           implementation_loss_db=0,
                           noise_bw_khz=60e3,
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
