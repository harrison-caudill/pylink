#!/usr/bin/python

import pylink
from pylink import TaggedAttribute as TA

def __do_it_do_it_now(self):
    return self.whimsy_coefficient

ex = {
    'whimsy_coefficient': TA(42,
                             datasheet="hitchhiker's guide to the galaxy",
                             author="Douglas Adams"),
    'wacky_computation': __do_it_do_it_now
    }


m = pylink.DAGModel([pylink.Geometry(),
                     pylink.Transmitter(tx_power_at_pa_dbw=2),
                     pylink.Interconnect(is_rx=False),
                     pylink.Antenna(is_rx=False),
                     pylink.Receiver(),
                     pylink.Antenna(is_rx=True),
                     pylink.Interconnect(is_rx=True),
                     pylink.Channel(),
                     pylink.Modulation('DVB-S2X'),
                     pylink.LinkBudget()],
                    **ex)
e = m.enum

print 'slant range (km):        %3g' % m.slant_range_km
print 'antenna angle (deg):     %3g' % m.satellite_antenna_angle_deg
print 'total rx noise temp (K): %3g' % m.rx_noise_temp_k
print 'receiver noise temp (K): %3g' % m.rx_system_noise_temp_k
print 'noise factor:            %3g' % m.rx_system_noise_factor
print 'noise figure (dB):       %3g' % m.rx_system_noise_figure
print 'transmit power (dBW):    %3g' % m.tx_power_at_antenna_dbw
print 'transmit eirp (dBW):     %3g' % m.tx_eirp_dbw
print 'UGPL (dB):               %3g' % m.unity_gain_propagation_loss_db
print 'Total Channel Loss (dB): %3g' % m.total_channel_loss_db
print 'Link Margin (dB):        %3g' % m.link_margin_db
print 'Noise BW Loss (dB):      %-3g' % m.excess_noise_bandwidth_loss_db
print 'Whimsical Value:         %d' % m.whimsy_coefficient
print 'Whimsical Info:          %s' % m.get_meta(e.whimsy_coefficient)
