#!/usr/bin/env python

import os
import pylink
import subprocess


from eg_budgets import DOWNLINK


"""Example of creating a dependency graph.

Graph visualizations can be useful for making alternations and
understanding the critical factors in computations.
"""

m = DOWNLINK


# This example is designed to place the result in the export directory
output_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),'export')
dotpath = os.path.join(output_dir, 'graph.dot')
pngpath = os.path.join(output_dir, 'graph.png')
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Force the system to calcluate all the necessary dependencies since
# they are computed at runtime
m.max_bitrate_hz
m.link_margin_db


with open(dotpath, 'w') as fd:
    fd.write(m.export_deps_dot())

subprocess.call(['gv', '-o', pngpath, dotpath])
