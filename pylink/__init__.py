#!/usr/bin/python

"""Link Budget Management in Python

This package provides a flexible system with which to build and solve
any Directed Acyclic Graph data model.  The design objective is to
hide the complexity of calculation in discrete segments all registered
through a simple central interface.  See the package README for more
details, the examples directory in the source code for how to use it.

IGNORE THE 'PACKAGE CONTENTS'.  Python is annoying, here's what you
can look up if you're interested:

=== Tributaries ===
Antenna
LinkBudget
Channel
Geometry
Interconnect
Code
Modulation
Receiver
Transmitter

=== Other Objects ===
Element
DAGModel
LoopException
BitrateFigure
CanonicalPFDFigure
ExpectedPFDFigure
PFDvsBWFigure
BitrateFigure
Report
TaggedAttribute

=== Utility Functions ===
to_db
from_db
spreading_loss_db
pattern_generator
rx_pfd_hz_adjust
tx_pfd_hz_adjust
e_field_to_eirp_dbw
eirp_dbw_to_e_field_v_per_m
human_hz
human_m
"""

__title__ = 'pylink'
__author__ = 'Harrison Caudill <harrison@hypersphere.org>'
__version__ = '0.3'
__copyright__ = 'Copyright 2016, Spire Global Inc, All Rights Reserved'


from element import Element
from model import DAGModel
from model import LoopException
from report import BitrateFigure
from report import CanonicalPFDFigure
from report import ExpectedPFDFigure
from report import PFDvsBWFigure
from report import BitrateFigure
from report import Report
from tagged_attribute import TaggedAttribute
from utils import to_db
from utils import from_db
from utils import spreading_loss_db
from utils import pattern_generator
from utils import rx_pfd_hz_adjust
from utils import tx_pfd_hz_adjust
from utils import e_field_to_eirp_dbw
from utils import eirp_dbw_to_e_field_v_per_m
from utils import human_hz
from utils import human_m
from utils import human_b


from tributaries.antenna import Antenna
from tributaries.budget import LinkBudget
from tributaries.channel import Channel
from tributaries.geometry import Geometry
from tributaries.interconnect import Interconnect
from tributaries.modulation import Code
from tributaries.modulation import Modulation
from tributaries.modulation import NORMAL_DVBS2X_PERFORMANCE
from tributaries.modulation import PERFECT_DVBS2X_PERFORMANCE
from tributaries.receiver import Receiver
from tributaries.transmitter import Transmitter
from tributaries.hyperspectral import HyperSpectralSNRBudget
