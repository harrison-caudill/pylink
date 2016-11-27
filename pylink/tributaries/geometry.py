#!/usr/bin/python

import math

from .. import utils


def _mean_orbit_altitude_km(model):
    return (model.apoapsis_altitude_km + model.periapsis_altitude_km) / 2


def _geo_altitude_km(model):
    return model.geo_radius_km - model.earth_radius_km


def _tx_distance_to_geo_km(model):
    # FIXME: rename to show it is the smallest value
    distance = model.geo_altitude_km
    if model.is_downlink:
        distance -= model.apoapsis_altitude_km
    return distance


def _slant_range_km(model):
    R = model.earth_radius_km
    h = model.mean_orbit_altitude_km + R
    e = math.radians(model.min_elevation_deg)
    return R * ((((h**2/R**2)-(math.cos(e))**2)**0.5) - math.sin(e))


def _periapsis_slant_range_km(model):    
    R = model.earth_radius_km
    h = model.periapsis_altitude_km + R
    e = math.radians(model.min_elevation_deg)
    return R * ((((h**2/R**2)-(math.cos(e))**2)**0.5) - math.sin(e))


def _satellite_antenna_angle_deg(model):
    R = model.earth_radius_km
    h = model.mean_orbit_altitude_km + R
    e = math.radians(model.min_elevation_deg)
    r = model.slant_range_km
    tmp = min(1.0, ((r**2+h**2-R**2)/(2*r*h)))
    return math.degrees(math.acos(tmp))


class Geometry(object):

    def __init__(self,
                 apoapsis_altitude_km=650,
                 periapsis_altitude_km=650,
                 min_elevation_deg=10,
                 earth_radius_km=6378.14,
                 geo_radius_km=42164):

        self.tribute = {
            # calculators
            'slant_range_km': _slant_range_km,
            'satellite_antenna_angle_deg': _satellite_antenna_angle_deg,
            'mean_orbit_altitude_km': _mean_orbit_altitude_km,
            'geo_altitude_km': _geo_altitude_km,
            'tx_distance_to_geo_km': _tx_distance_to_geo_km,
            'periapsis_slant_range_km': _periapsis_slant_range_km,

            # constants
            'geo_radius_km': geo_radius_km,
            'apoapsis_altitude_km': apoapsis_altitude_km,
            'periapsis_altitude_km': periapsis_altitude_km,
            'earth_radius_km': earth_radius_km,
            'min_elevation_deg': min_elevation_deg,
            }
