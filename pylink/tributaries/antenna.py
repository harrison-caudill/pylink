#!/usr/bin/python

import scipy
import scipy.interpolate
import scipy.signal
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import math

from ..model import DAGModel
from .. import utils


def _floor(v, n):
    return int(n * math.floor(v/n))


def _find_nearest_index(array, value):
    value = (360 + value) % 360
    return np.abs(array - value).argmin()


def _average_gain_dbi(pattern, angles):
    return sum(pattern) / float(len(pattern))


def _average_nadir_gain_dbi(pattern, angles):
    """Average gain on the nadir face of the satellite.

    For simplicity, this function assumes some hard-coded values of
    65-degrees off of boresight.  That translates to 0->65 and (360-65)->360
    """
    s = 0
    n = 0
    offset = 65
    for i in range(len(pattern)):
        angle = angles[i]
        gain = pattern[i]
        if (0 <= angle <= offset) or ((360-offset) <= angle <= 360):
            s += gain
            n += 1
    return s / n


class Antenna(object):
    """Antenna tributary

    This class can be used either for tx or for rx and it will
    register its functions as either the tx_antenna_... or
    rx_antenna_... as appropriate.
    """

    def __init__(self,
                 pattern=None,
                 gain=0.0,
                 polarization='RHCP',
                 tracking=True,
                 rf_chain=[],
                 pointing_loss_db=0,
                 is_rx=True,
                 **meta):
        """Create a new antenna tributary.

        pattern -- list of evenly-spaced pattern cut values starting at 0
        gain -- peak gain of the antenna
        polarization -- str
        tracking -- does it track the target (eg rotator) or not (eg nadir)
        rf_chain -- list of Element objects for the RF hain on the board
        pointing_loss_db -- for now, just the number of dB of pointing loss
        is_rx -- is it for receive or transmit
        kwargs -- any metadata to assign to the antenna itself

        If there are 360 points in the pattern, it will be
        interpolated for you automatically.
        """

        self.meta = meta

        self.peak_gain_only = (pattern is None)
        if pattern is None:
            self.peak_gain_only = True
            self.peak_gain = gain
            pattern = np.zeros(360)
            pattern += gain
        else:
            self.peak_gain = max(pattern)

        pattern = np.array(pattern)

        self.pattern_angles = np.arange(0.0, 360.0, 360.0/len(pattern))
        self.pattern = pattern

        if len(pattern) == 360:
            self.interpolated = pattern[:]
            self.interpolated_angles = np.arange(0, 360, 1)
        else:
            interpolated = self._interpolate_pattern(pattern)
            self.interpolated_angles = np.arange(0, 360, 360/len(interpolated))
            self.interpolated = interpolated

        self.is_rx = is_rx

        self.tribute = {
            # calculators
            self._mangle('peak_gain_dbi'): self._peak_gain_dbi,
            self._mangle('gain_dbi'): self._gain_dbi,
            self._mangle('angle_deg'): self._angle_deg,
            self._mangle('boresight_gain_dbi'): self._boresight_gain_dbi,
            self._mangle('average_gain_dbi'): self._average_gain_dbi,
            self._mangle('average_nadir_gain_dbi'): self._average_nadir_gain_dbi,

            # constants
            self._name('polarization'): polarization,
            self._name('raw_gain_pattern'): pattern,
            self._name('raw_gain_pattern_angles'): self.pattern_angles,
            self._name('gain_pattern'): self.interpolated,
            self._name('gain_pattern_angles'): self.interpolated_angles,
            self._name('obj'): self,
            self._name('tracking_target'): not not tracking,
            self._name('rf_chain'): rf_chain,
            self._name('pointing_loss_db'): pointing_loss_db,
            }

    def _name(self, s):
        if self.is_rx:
            return 'rx_antenna_'+s
        else:
            return 'tx_antenna_'+s

    def _lst_to_rad(self, lst):
        return np.array([math.radians(v) for v in lst])

    def _wrap(self, lst):
        return np.array(list(lst) + [lst[0]])

    def _plot_peak_gain(self, fname, title):
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1, projection='polar')

        theta = self._lst_to_rad(self.pattern_angles[:])
        pattern = np.array(self.pattern)

        # offset the pattern to get around the negative-radius issue
        if self.peak_gain < 0:
            offset = -2 * self.peak_gain
            pattern += offset

        ax.plot(theta,
                pattern,
                color='r',
                linewidth=3,
                label='Peak Gain Used Everywhere')
        fig.canvas.draw()
        if self.peak_gain < 0:
            ax.set_yticklabels([t - offset for t in ax.get_yticks()])

        fig.suptitle(title)
        plt.legend(loc=4)

        fig.savefig(fname, transparent=True)

    def _plot_interpolated(self, fname, title, include_raw, ylim):
        # Wrap around one point to close the loop and convert to radians
        interp = self._wrap(self.interpolated)
        raw = np.copy(self.pattern)

        low = min(min(interp), min(raw))
        hi = max(min(interp), max(raw))

        n_steps = 5
        min_step_size = 1
        step_size = max(int((hi - low) / n_steps), min_step_size)

        low_r = _floor(low, step_size)
        hi_r = _floor(hi, step_size)

        val_start = low_r if low_r < low else low_r - step_size
        val_stop = hi_r + step_size

        offset = 0 - val_start

        # to debug uncomment these lines
        # print 'low:         %s' % low
        # print 'hi:          %s' % hi
        # print 'low_r:       %s' % low_r
        # print 'hi_r:        %s' % hi_r
        # print 'val_start:   %s' % val_start
        # print 'val_stop:    %s' % val_stop
        # print 'step_size:   %s' % step_size
        # print 'offset:      %s' % offset
        # print

        interp += offset
        raw += offset

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1, projection='polar')

        if ylim:
            locator = matplotlib.ticker.MaxNLocator(nbins=8)
            ax.yaxis.set_major_locator(locator)            
            ax.set_ylim([ylim[0]+offset, ylim[1]+offset])

        interp_angles = self._wrap(self._lst_to_rad(self.interpolated_angles))
        raw_angles = self._lst_to_rad(self.pattern_angles)

        include_raw = (include_raw
                       and (len(self.pattern) != len(self.interpolated)))

        if len(self.pattern) == len(self.interpolated):
            label = 'Antenna Pattern'
            main_angles = raw_angles
            main_pattern = raw
        else:
            label = 'Interpolated Pattern'
            main_angles = interp_angles
            main_pattern = interp


        ax.set_theta_zero_location("N")

        ax.plot(main_angles,
                main_pattern,
                color='r',
                linewidth=3,
                label=label)

        if include_raw:
            ax.plot(raw_angles,
                    raw, 'x',
                    color='b',
                    linewidth=1,
                    label='Observed')
        fig.canvas.draw()

        ax.set_yticklabels([t - offset for t in ax.get_yticks()])

        fig.suptitle(title)
        plt.legend(loc=4)

        fig.savefig(fname, transparent=True)

    def plot_pattern(self, fname, include_raw=True, title=None, ylim=None):
        """Plots the pattern to a PNG file.

        fname -- where to save it
        include_raw -- If the pattern is interpolated, include the raw points?
        title -- Title of the image
        ylim -- [min, max] as desired

        If, for example, your real pattern varies by only one dB, its
        plot can be correct, but look a little weird as you see it
        vary wildly from one side to the other whereas it is quite
        stable in reality.  Thtat's why the <ylim> is an option.
        """

        prefix = 'RX' if self.is_rx else 'TX'
        if not title:
            title = '%s Antenna Gain Pattern' % prefix

        if self.peak_gain_only:
            return self._plot_peak_gain(fname, title)
        else:
            return self._plot_interpolated(fname, title, include_raw, ylim)

    def _linear_interpolate(self, src, factor):
        src_x = np.arange(0, len(src), 1)
        tck = scipy.interpolate.splrep(src_x, src, s=0)
        dst_x = np.arange(0, len(src), 1.0/factor)
        dst = scipy.interpolate.splev(dst_x, tck, der=0)
        return dst

    def _circular_interpolate(self, src, factor):
        tmp = list(src)*3
        tmp = self._linear_interpolate(tmp, factor)
        l = int(len(tmp) / 3)
        return tmp[l:2*l]

    def _interpolate_pattern(self, pattern, factor=None):
        if not factor:
            # default to roughly every one degree
            factor = (360.0 / len(pattern))
        return self._circular_interpolate(pattern, factor)

    def _mangle(self, name):
        x = 'rx' if self.is_rx else 'tx'
        s = '_' if name[0] == '_' else ''
        return '%s%s_antenna_%s' % (s, x, name)

    def _call(self, model, name):
        return getattr(model, self._mangle(name))

    def _peak_gain_dbi(self, model):
        return max(self._call(model, 'gain_pattern'))

    def _gain_dbi(self, model):
        if self._call(model, 'tracking_target'):
            return self._call(model, 'boresight_gain_dbi')
        else:
            angle = self._call(model, 'angle_deg')
            angles = self._call(model, 'gain_pattern_angles')
            idx = _find_nearest_index(angles, angle)
            pattern = self._call(model, 'gain_pattern')
            return pattern[idx]

    def _angle_deg(self, model):
        if self._call(model, 'tracking_target'):
            return 0

        if model.is_downlink:
            if self.is_rx:
                # We are the ground-station
                return model.min_elevation_deg
            else:
                # We are the satellite
                return model.satellite_antenna_angle_deg
        else:
            if self.is_rx:
                # We are the satellite
                return model.satellite_antenna_angle_deg
            else:
                # We are the ground-station
                return model.min_elevation_deg

    def _boresight_gain_dbi(self, model):
        pattern = self._call(model, 'gain_pattern')
        angles = self._call(model, 'gain_pattern_angles')
        idx = _find_nearest_index(angles, 0)
        return pattern[idx]

    def _average_gain_dbi(self, model):
        pattern = self._call(model, 'gain_pattern')
        angles = self._call(model, 'gain_pattern_angles')
        return _average_gain_dbi(pattern, angles)

    def _average_nadir_gain_dbi(self, model):
        pattern = self._call(model, 'gain_pattern')
        angles = self._call(model, 'gain_pattern_angles')
        return _average_nadir_gain_dbi(pattern, angles)
