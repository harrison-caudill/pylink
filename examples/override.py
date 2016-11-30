#!/usr/bin/python

import pylink

"""Illustrations of the override functionality.

This example illustrates how node values can be overridden.
"""

def _the_calculated_answer(model):
    return 42

def _the_answer_plus_two(model):
    return model.the_answer + 2

m = pylink.DAGModel(the_answer=42,
                    the_calculated_answer=_the_calculated_answer,
                    the_answer_plus_two=_the_answer_plus_two)
e = m.enum

print 'The original answer:', m.the_answer
print 'Overriding the Answer to 24'
m.override(e.the_answer, 24)
print 'The new answer:', m.the_answer
print 'The override value:', m.override_value(e.the_answer)

print ''

print '"Reverting" the override is illegal, since it is a static value'
try:
    m.revert(e.the_answer)
except AttributeError, err:
    print 'Caught an AttributeError: "%s"' % err

print ''

print 'If, however, you wanted to do that with a calculated node:'
print 'The original answer:', m.the_calculated_answer
print 'Overriding the Answer to 24'
m.override(e.the_calculated_answer, 24)
print 'The new "calculated" answer:', m.the_calculated_answer
print 'The override value:', m.override_value(e.the_calculated_answer)
print 'Reverting'
m.revert(e.the_calculated_answer)
print 'The override value after clearing:', m.override_value(e.the_calculated_answer)
print 'The answer after clearing the override:', m.the_calculated_answer
