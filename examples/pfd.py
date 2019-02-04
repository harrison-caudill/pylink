#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import inspect

import pylink

from eg_budgets import DOWNLINK

m = DOWNLINK
e = m.enum

restrictions = [
    # (start-deg, start-value, end-deg, end-value)
    (0, -152),
    (5, -152),
    (25, -142),
    (90, -142),
    ]

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

x = [p[0] for p in restrictions]
y = [p[1] for p in restrictions]
plt.plot(x, y, color='r', linewidth=2, label='Limit')
ax.set_xlabel('Elevation Angle (degrees)')
ax.set_ylabel('Boresight PFD (dBW/m^2/%d%s)' % pylink.human_hz(4000))

x = np.linspace(10.0, 90.0)
y = np.linspace(10.0, 90.0)
for i in range(len(x)):
    m.override(e.min_elevation_deg, x[i])
    pfd = m.pfd_dbw_per_m2_per_hz + pylink.to_db(4000)
    y[i] = pfd

low = min(min(y), min([v[1] for v in restrictions]))
hi = max(max(y), max([v[1] for v in restrictions]))

delta = (hi - low) * 0.1
low -= delta
hi += delta

ax.set_ylim(low, hi)

plt.plot(x, y)

d = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'export')
f = os.path.join(d, 'pfd.png')
if not os.path.exists(d):
    os.makedirs(d)
fig.savefig(f)
print("PFD Plot Generated at: %s" % f)
