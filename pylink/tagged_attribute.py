#!/usr/bin/python


class TaggedAttribute(object):
    """Simple container object to tag values with attributes.

    Feel free to initialize any node with a TA instead of its actual
    value only and it will then have the desired metadata.  For example:

    from pylink import TaggedAttribute as TA
    tx_power = TA(2,
                  part_number='234x',
                  test_report='http://reports.co/234x')
    m = DAGModel([pylink.Transmitter(tx_power_at_pa_dbw=tx_power)])
    """

    def __init__(self, value, **kwargs):
        self.meta = kwargs
        self.value = value
