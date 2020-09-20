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
__version__ = '0.9'
__license__ = 'BSD'


from pylink.element import Element
from pylink.model import DAGModel
from pylink.model import LoopException
from pylink.report import BitrateFigure
from pylink.report import CanonicalPFDFigure
from pylink.report import ExpectedPFDFigure
from pylink.report import PFDvsBWFigure
from pylink.report import BitrateFigure
from pylink.report import Report
from pylink.tagged_attribute import TaggedAttribute
from pylink.utils import to_db
from pylink.utils import from_db
from pylink.utils import spreading_loss_db
from pylink.utils import pattern_generator
from pylink.utils import rx_pfd_hz_adjust
from pylink.utils import tx_pfd_hz_adjust
from pylink.utils import e_field_to_eirp_dbw
from pylink.utils import eirp_dbw_to_e_field_v_per_m
from pylink.utils import human_hz
from pylink.utils import human_m
from pylink.utils import human_b

from pylink.tributaries.antenna import Antenna
from pylink.tributaries.budget import LinkBudget
from pylink.tributaries.channel import Channel
from pylink.tributaries.geometry import Geometry
from pylink.tributaries.interconnect import Interconnect
from pylink.tributaries.modulation import Code
from pylink.tributaries.modulation import Modulation
from pylink.tributaries.modulation import NORMAL_DVBS2X_PERFORMANCE
from pylink.tributaries.modulation import PERFECT_DVBS2X_PERFORMANCE
from pylink.tributaries.receiver import Receiver
from pylink.tributaries.transmitter import Transmitter
from pylink.tributaries.hyperspectral import HyperSpectralSNRBudget
