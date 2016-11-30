#!/usr/bin/python

import pylink


def _raises_exception(model):
    """Return a value that doesn't exist.

    Calling this node will result in an AttributeError because the
    'does_not_exist' node, well, doesn't exist.
    """
    return model.does_not_exist


extras = {'raises_exception': _raises_exception}
m = pylink.DAGModel([], **extras)

print "="*80
print 'AttributeError will be raised'
print "We're asking for a node that doesn't exist"
print "="*80
print m.raises_exception
