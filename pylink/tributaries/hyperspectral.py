#!/usr/bin/python

import argparse
import numpy as np
import pylink
import math
import jinja2
import matplotlib.pyplot as plt


def _interpolate(tgt, vals, off):
    def __search(tgt, vals):
        low = 0
        hi = len(vals)
        cur = int(hi/2)
        while (hi - low) > 1:
            if vals[cur][0] > tgt:
                hi = cur
                cur = int(low + (cur - low)/2)
            elif vals[cur][0] < tgt:
                low = cur
                cur = int(cur + (hi - cur)/2)
            elif vals[cur][0] == tgt:
                return cur
        return low

    lo = __search(tgt, vals)

    # correct value
    if vals[lo][0] == tgt:
        return vals[lo][off]

    hi = lo + 1
    x0 = vals[lo][0]
    x1 = vals[hi][0]
    y0 = vals[lo][off]
    y1 = vals[hi][off]
    rate = (y1-y0)/(x1-x0)
    return rate*(tgt-x0)+y0


class HyperSpectralSNRBudget(object):

    def __init__(self,
                 orbital_solar_irradiance,
                 ground_solar_irradiance,
                 reflectance_db=pylink.to_db(0.5),
                 fore_optics_efficiency_db=pylink.to_db(0.95),
                 focusing_optics_efficiency_db=pylink.to_db(0.95),
                 grating_efficiency_db=pylink.to_db(0.8),
                 sensor_quantum_efficiency_db=pylink.to_db(0.8),
                 read_out_noise_e=50,
                 pixel_pitch_um=15,
                 fwhm_nm=10,
                 gsd_m=15,
                 gmc=1,
                 lambda_nm=1990,
                 lens_radius_m=0.3,
                 bits_per_sample=12,
                 spatial_channels=640):

        self.tribute = {
            # Constants
            'orbital_solar_irradiance_w': orbital_solar_irradiance,
            'ground_solar_irradiance_w': ground_solar_irradiance,
            'speed_of_light_m_s': 299792458,
            'plancks_constant': 6.626068*10**-34,
            'grav_const': 6.67*10**-11,
            'earth_mass_kg': 5.98*10**24,
            'reflectance_db': reflectance_db,
            'fore_optics_efficiency_db': fore_optics_efficiency_db,
            'grating_efficiency_db': grating_efficiency_db,
            'focusing_optics_efficiency_db': focusing_optics_efficiency_db,
            'sensor_quantum_efficiency_db': sensor_quantum_efficiency_db,
            'read_out_noise_e': read_out_noise_e,
            'pixel_pitch_um': pixel_pitch_um,
            'fwhm_nm': fwhm_nm,
            'gsd_m': gsd_m,
            'gmc': gmc,
            'lambda_nm': lambda_nm,
            'lens_radius_m': lens_radius_m,
            'bits_per_sample': bits_per_sample,
            'spatial_channels': spatial_channels,

            # Calculators
            'incident_power_flux_density_dbw_m2_nm': self._incident_power_flux_density_dbw_m2_nm,
            'reflected_power_flux_density_dbw_m2_nm': self._reflected_power_flux_density_dbw_m2_nm,
            'reflected_power_density_dbw_nm': self._reflected_power_density_dbw_nm,
            'reflected_power_dbw': self._reflected_power_dbw,
            'power_flux_at_lens_dbw_m2': self._power_flux_at_lens_dbw_m2,
            'received_power_dbw': self._received_power_dbw,
            'orbital_velocity_km_per_s': self._orbital_velocity_km_per_s,
            'orbital_period_s': self._orbital_period_s,
            'shutter_time_s': self._shutter_time_s,
            'energy_at_sensor_dbj': self._energy_at_sensor_dbj,
            'signal_electrons_in_well_dbe': self._signal_electrons_in_well_dbe,
            'noise_electrons_dbe': self._noise_electrons_dbe,
            'snr_db': self._snr_db,
            'ground_area_dbm2': self._ground_area_dbm2,
            'optical_loss_db': self._optical_loss_db,
            'atmospheric_loss_db': self._atmospheric_loss_db,
            }

    def _incident_power_flux_density_dbw_m2_nm(self, model):
        PFD = max(_interpolate(model.lambda_nm,
                               model.ground_solar_irradiance_w,
                               1),
                  1e-10)
        return pylink.to_db(PFD)

    def _reflected_power_flux_density_dbw_m2_nm(self, model):
        # Incoming Power Flux
        Pi = model.incident_power_flux_density_dbw_m2_nm

        # Lambertian Reflectance (dimensionless)
        Rl = model.reflectance_db

        # Reflected Power Flux
        Pr = Pi + Rl

        return Pr

    def _ground_area_dbm2(self, model):
        return pylink.to_db(model.spatial_channels * model.gsd_m**2)

    def _reflected_power_density_dbw_nm(self, model):
        return (0.0
                + model.reflected_power_flux_density_dbw_m2_nm
                + model.ground_area_dbm2)

    def _reflected_power_dbw(self, model):
        return (1.0
                + model.reflected_power_density_dbw_nm
                + pylink.to_db(model.fwhm_nm))

    def _atmospheric_loss_db(self, model):
        # Power incident on the atmosphere
        Pi = _interpolate(model.lambda_nm,
                          model.orbital_solar_irradiance_w,
                          1)
        Pi = pylink.to_db(Pi)

        # Power transmitted through the atmosphere
        Pt = model.incident_power_flux_density_dbw_m2_nm

        return Pi - Pt

    def _power_flux_at_lens_dbw_m2(self, model):
        # Approximate the pixel as a point source and apply spreading loss
        # The approsimate transmission gain is 3dB as lambertian reflectors
        D = model.slant_range_km*1000
        spreading_loss_db = pylink.to_db(math.pi*2*D**2)
        return (0.0
                + model.reflected_power_dbw
                - spreading_loss_db
                - model.atmospheric_loss_db)

    def _received_power_dbw(self, model):
        # Incident Power Flux
        Pi = model.power_flux_at_lens_dbw_m2

        # Collecting Aperture Area
        A = pylink.to_db(math.pi * model.lens_radius_m**2)

        return Pi + A

    def _orbital_velocity_km_per_s(self, model):
        G = model.grav_const
        M = model.earth_mass_kg
        Re = model.earth_radius_km
        Alt = model.mean_orbit_altitude_km
        R = 1000 * (Re + Alt)
        return (G * M / R)**.5 / 1000.0

    def _orbital_period_s(self, model):
        v = model.orbital_velocity_km_per_s * 1000
        Re = model.earth_radius_km
        Alt = model.mean_orbit_altitude_km
        R = 1000 * (Re + Alt)
        return 2 * math.pi * R / v

    def _shutter_time_s(self, model):
        # Great Circle Circumference (m)
        Gc = model.earth_radius_km * 1000 * math.pi * 2

        # Orbital Period
        To = model.orbital_period_s

        # Ground Speed
        Gs = Gc / To

        # Time required to traverse the GSD
        T = model.gsd_m / Gs

        # GMC Factor
        return T * model.gmc

    def _optical_loss_db(self, model):
        # These efficiencies are all negative numbers, and this
        # function is meant to return a positive number (ie dB's of
        # loss as opposed to dB's of transmission), so we multiply by
        # negative 1.
        return -1 * (0.0
                     + model.fore_optics_efficiency_db
                     + model.grating_efficiency_db
                     + model.focusing_optics_efficiency_db)

    def _energy_at_sensor_dbj(self, model):
        # Energy striking the primary lens
        P_lens = model.received_power_dbw + pylink.to_db(model.shutter_time_s)

        # Optical losses associated with inefficiencies
        # Losses associated with the focal plane sensor
        P_sensor = P_lens - model.optical_loss_db

        return P_sensor

    def _signal_electrons_in_well_dbe(self, model):
        E_sensor = model.energy_at_sensor_dbj
        E_pixel = E_sensor - pylink.to_db(model.spatial_channels)
        P_r = E_pixel + model.sensor_quantum_efficiency_db
        lambda_dbm = pylink.to_db(model.lambda_nm) - 90
        h_db = pylink.to_db(model.plancks_constant)
        c_db = pylink.to_db(model.speed_of_light_m_s)
        return P_r + lambda_dbm - h_db - c_db

    def _noise_electrons_dbe(self, model):
        N = (0.0
             + model.read_out_noise_e
             + pylink.from_db(model.signal_electrons_in_well_dbe/2))
        return pylink.to_db(N)

    def _snr_db(self, model):
        return model.signal_electrons_in_well_dbe - model.noise_electrons_dbe
