#!/usr/bin/python

import argparse
import csv
import matplotlib.pyplot as plt
import numpy as np
import os
import pylink


def _load_irradiance(path, n=1):
    with open(path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        header = None
        tmp = []
        for row in reader:
            if not header:
                header = row
            else:
                lam = row[0]
                irradiance = row[n]
                tmp.append([lam, irradiance])
    retval = np.zeros((len(tmp), 2,))
    for i in range(len(tmp)):
        retval[i][0] = tmp[i][0] # lambda
        retval[i][1] = tmp[i][1] # irradiance
    return retval


def plot_snr(model,
             path=None,
             start_nm=400,
             end_nm=2500,
             title=None,
             twin=False,
             pixels=True):
    m = model
    e = m.enum

    # rename these for convenience
    xmin = start_nm
    xmax = end_nm

    if not path:
        path = 'snr_%d_%d.png' % (xmin, xmax)

    if not title:
        title = 'SNR %dnm - %dnm %dkm' % (xmin, xmax, m.mean_orbit_altitude_km)

    fig = plt.figure()
    fig.suptitle(title)
    ax1 = fig.add_subplot(1, 1, 1)

    x = range(xmin, xmax, 1)
    y = np.zeros(len(x))
    yi = np.zeros(len(x))
    ydb = np.zeros(len(x))
    for i in range(len(x)):
        m.override(e.lambda_nm, x[i])
        snr_db = m.snr_db
        ydb[i] = snr_db
        y[i] = pylink.from_db(snr_db)
        yi[i] = m.incident_power_flux_density_dbw_m2_nm
    ax1.plot(x, y, color='r', label='SNR')
    ax1.set_ylabel('SNR')

    ax1.set_xlabel('Lambda (nm)')

    if twin:
        ax2 = ax1.twinx()
        for i in range(len(x)):
            m.override(e.lambda_nm, x[i])
            snr_db = m.snr_db
            ydb[i] = snr_db
            y[i] = pylink.from_db(snr_db)
        ax2.plot(x, yi, color='b', label='SNR (dB)')
        ax2.set_ylabel('Solar Irradiance at Ground (W/m^2/nm)', color='b')

    if pixels:
        xpix = []
        ypix = []
        cur = xmin
        i = 0
        while cur < xmax:
            snr = sum(y[i:i+m.fwhm_nm]) / min(m.fwhm_nm, xmax-cur)
            xpix.append(cur+int(m.fwhm_nm/2))
            ypix.append(snr)
            cur += m.fwhm_nm
            i += m.fwhm_nm
        ax1.plot(xpix, ypix, '+', color='b', label='Pixel SNR')


    fig.legend()

    print('Plotting SNR for %dnm-%dnm in %s' % (
        start_nm, end_nm, path))
    fig.savefig(path)


if __name__ == '__main__':
    desc = """Builds an Example SNR Budget

Here we use ASTM G173-03 Reference Spectra Derived from SMARTS
v. 2.9.2

The original html file (included in the repository) was obtained on
Friday, February 8th from
https://rredc.nrel.gov/solar//spectra/am1.5/ASTMG173.html


"""
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--atmosphere-irradiance-csv', '-a',
                        metavar='ATMOSPHERE_IRRADIANCE_CSV',
                        action='store',
                        dest='atmo_path',
                        required=False,
                        type=str,
                        default='astmg173.csv',
                        help='Full input path for the atmospheric irradiance CSV file',)

    parser.add_argument('--atmosphere-irradiance-index', '-A',
                        metavar='ATMOSPHERE_IRRADIANCE_INDEX',
                        action='store',
                        dest='atmo_index',
                        required=False,
                        type=int,
                        default=1,
                        help='Index into CSV for the atmospheric irradiance',)

    parser.add_argument('--ground-irradiance-csv', '-g',
                        metavar='GROUND_IRRADIANCE_CSV',
                        action='store',
                        dest='ground_path',
                        required=False,
                        type=str,
                        default='astmg173.csv',
                        help='Full input path for the ground irradiance CSV file',)

    parser.add_argument('--ground-irradiance-index', '-G',
                        metavar='GROUND_IRRADIANCE_INDEX',
                        action='store',
                        dest='ground_index',
                        required=False,
                        type=int,
                        default=3,
                        help='Index into the CSV for the ground irradiance',)

    args = parser.parse_args()

    atmo_irradiance = _load_irradiance(args.atmo_path, args.atmo_index)
    ground_irradiance = _load_irradiance(args.ground_path, args.ground_index)

    budget = pylink.HyperSpectralSNRBudget(atmo_irradiance, ground_irradiance)

    geometry = pylink.Geometry(apoapsis_altitude_km=500,
                               periapsis_altitude_km=500,
                               min_elevation_deg=90)

    m = pylink.DAGModel([budget, geometry])
    e = m.enum

    output_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'export')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    path = os.path.join(output_dir, 'snr-vnir.png')
    plot_snr(m, start_nm=400,  end_nm=1400,  path=path)
