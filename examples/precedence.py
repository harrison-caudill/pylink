#!/usr/bin/env python

import pylink

"""Illustrations of the precedence order for node definitions.

Nodes are added to the DAG in the order in which they are received.
So you can, if you wish, override a standard definition.
"""

# Vanilla link budget
m = pylink.DAGModel([pylink.Geometry(),
                     pylink.Transmitter(tx_power_at_pa_dbw=2),
                     pylink.Interconnect(is_rx=False),
                     pylink.Antenna(is_rx=False),
                     pylink.Receiver(),
                     pylink.Antenna(is_rx=True),
                     pylink.Interconnect(is_rx=True),
                     pylink.Channel(),
                     pylink.Modulation('DVB-S2X'),
                     pylink.LinkBudget()])
e = m.enum

print('Link margin in vanilla example: %s' % m.link_margin_db)

# let's override the link_margin_db node in the kwargs
def _evil_margin_db(model):
    return -3.0
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
                    link_margin_db=_evil_margin_db)
e = m.enum
print('Link margin after overriding the node: %s' % m.link_margin_db)


# let's override the link_margin_db node in a tributary
class EvilMargin(object):
    def __init__(self):
        self.tribute = {'link_margin_db': _evil_margin_db}
m = pylink.DAGModel([pylink.Geometry(),
                     pylink.Transmitter(tx_power_at_pa_dbw=2),
                     pylink.Interconnect(is_rx=False),
                     pylink.Antenna(is_rx=False),
                     pylink.Receiver(),
                     pylink.Antenna(is_rx=True),
                     pylink.Interconnect(is_rx=True),
                     pylink.Channel(),
                     pylink.Modulation('DVB-S2X'),
                     pylink.LinkBudget(),
                     EvilMargin()])
e = m.enum
print('Link margin after a tributary-override: %s' % m.link_margin_db)


# let's be evil dunces and have our evil function overridden by the
# standard tributary's node.
m = pylink.DAGModel([pylink.Geometry(),
                     pylink.Transmitter(tx_power_at_pa_dbw=2),
                     pylink.Interconnect(is_rx=False),
                     pylink.Antenna(is_rx=False),
                     pylink.Receiver(),
                     pylink.Antenna(is_rx=True),
                     pylink.Interconnect(is_rx=True),
                     pylink.Channel(),
                     pylink.Modulation('DVB-S2X'),
                     EvilMargin(),
                     pylink.LinkBudget()])
e = m.enum
print('Link margin after a failed tributary-override: %s' % m.link_margin_db)
