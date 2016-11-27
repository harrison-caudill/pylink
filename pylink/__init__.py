#!/usr/bin/python

"""Link Budget Management in Python

This package provides a flexible system with which to build and solve
any Directed Acyclic Graph data model.  The design objective is to
hide the complexity of calculation in discrete segments all registered
through a simple central interface.  See the package README for more
details, the examples directory in the source code for how to use it.
"""

__title__ = 'pylink'
__author__ = 'Harrison Caudill <harrison@hypersphere.org>'
__version__ = '0.3'
__copyright__ = 'Copyright 2016, Spire Global Inc, All Rights Reserved'


from element import Element
from model import DAGModel
from model import LoopException
from report import BitrateFigure
from report import PFDFigure
from report import Report
from tagged_attribute import TaggedAttribute
from utils import to_db
from utils import from_db
from utils import spreading_loss_db
from utils import pattern_generator

from tributaries.antenna import Antenna
from tributaries.budget import LinkBudget
from tributaries.channel import Channel
from tributaries.geometry import Geometry
from tributaries.interconnect import Interconnect
from tributaries.modulation import Code
from tributaries.modulation import Modulation
from tributaries.receiver import Receiver
from tributaries.transmitter import Transmitter
