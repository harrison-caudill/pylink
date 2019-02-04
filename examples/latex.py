#!/usr/bin/env python

import os

import pylink
from eg_budgets import DOWNLINK

m = DOWNLINK
e = m.enum
r = pylink.Report(m)
d = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'export')
f = os.path.join(d, 'test.tex')
if not os.path.exists(d):
    os.makedirs(d)
r.to_latex(f)
