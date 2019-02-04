#!/usr/bin/env python

import os
import pylink

d = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'export')
if not os.path.exists(d):
    os.makedirs(d)

for peak in [3, 5, 15]:
    eff = .65
    null = -20
    f = os.path.join(d, 'pattern-%ddBi.png' % peak)

    pattern = pylink.pattern_generator(peak, eff=eff, null=null)
    ant = pylink.Antenna(pattern=pattern)

    ant.plot_pattern(f,
                     include_raw=False,
                     title='%ddBi Generated Pattern' % peak,
                     ylim=[null-3, peak+3])
    print('Pattern Created: %s' % f)



f = os.path.join(d, 'pattern-manual.png')
pattern = [10, 5, -5, -9, -10, -10, -10, -10, -10, -10, -9, -5, 5]
ant = pylink.Antenna(pattern=pattern)
ant.plot_pattern(f,
                 include_raw=True,
                 title='Manual Pattern')
print('Pattern Created: %s' % f)

