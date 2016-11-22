#!/usr/bin/python

import pylink
from eg_budgets import DOWNLINK

m = DOWNLINK
e = m.enum

print 'PF (dbW/m^2):       %g' % m.pf_dbw_per_m2
print 'TX EIRP (dbW):      %g' % m.tx_eirp_dbw

new = m.solve_for(var=e.tx_eirp_dbw,
                  fixed=e.pf_dbw_per_m2,
                  fixed_value=-150,
                  start=-20,
                  stop=10,
                  step=0.177)
print 'Max EIRP (dbW):     %g' % new
m.override(e.tx_eirp_dbw, new)
print 'New PF (dbW/m^2):   %g' % m.pf_dbw_per_m2
