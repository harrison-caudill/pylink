#!/usr/bin/python

import argparse
import csv
import matplotlib.pyplot as plt
import numpy as np
import pylink


def _load_irradiance(path):
    with open(path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        header = None
        tmp = []
        for row in reader:
            if not header:
                header = row
            else:
                lam, irradiance = row
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
    fig.savefig(path)


if __name__ == '__main__':
    desc = """Builds an Example SNR Budget

The CSV files for both extra-atmospheric solar irradiance as well as
the irradiance at the ground must both be provided because the ASTM
requires a license for its use.  If anyone has a version that can be
included in PyLink for free, please pass it along to the author.
Otherwise, you can buy a copy from here:

https://www.astm.org/Standards/G173.htm

The CSV files should be of the form (including the header row):

lambda, irradiance,
280.0,2e-26
...

"""
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--atmosphere-irradiance-csv', '-a',
                        metavar='ATMOSPHERE_IRRADIANCE_CSV',
                        action='store',
                        dest='atmo_path',
                        required=False,
                        type=str,
                        default='atmospheric_irradiance.csv',
                        help='Full input path for the atmospheric irradiance CSV file',)

    parser.add_argument('--ground-irradiance-csv', '-g',
                        metavar='GROUND_IRRADIANCE_CSV',
                        action='store',
                        dest='ground_path',
                        required=False,
                        type=str,
                        default='ground_irradiance.csv',
                        help='Full input path for the ground irradiance CSV file',)

    args = parser.parse_args()

    atmo_irradiance = _load_irradiance(args.atmo_path)
    ground_irradiance = _load_irradiance(args.ground_path)

    budget = pylink.HyperSpectralSNRBudget(atmo_irradiance, ground_irradiance)

    geometry = pylink.Geometry(apoapsis_altitude_km=500,
                               periapsis_altitude_km=500,
                               min_elevation_deg=90)

    m = pylink.DAGModel([budget, geometry])
    e = m.enum

    plot_snr(m, start_nm=400,  end_nm=1400,  path='snr-vnir.png')
