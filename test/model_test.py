#!/usr/bin/python

import pylink
import pytest

from testutils import model


class TestOrbit(object):

    def test_loop_detection(self):
        def __a(model):
            return model.b

        def __b(model):
            return model.c

        def __c(model):
            return model.d

        def __d(model):
            return model.e

        def __e(model):
            return model.b

        # a -> b -> c -> d -> e
        #      ^              |
        #      |              |
        #      +--------------+

        m = pylink.DAGModel(a=__a, b=__b, c=__c, d=__d, e=__e)

        with pytest.raises(pylink.LoopException):
            m.a

    def test_basic_call(self):
        def __a(model):
            return model.b

        def __b(model):
            return 42

        m = pylink.DAGModel(a=__a, b=__b)
        assert 42 == m.a

    def test_basic_value(self):
        def __a(model):
            return model.b

        def __b(model):
            return 42

        m = pylink.DAGModel(a=__a, b=__b)
        assert 42 == m.a

    def _wrap_func(self, func, **wrap_kwargs):

        def retval(*args, **call_kwargs):
            kwargs = wrap_kwargs
            kwargs.update(call_kwargs)
            return func(*args, **kwargs)

        return retval

    def _tracking_calculator(self,
                             model,
                             state_var='_has_run',
                             deps=[],
                             retval=42):
        n = getattr(self, state_var)
        setattr(self, state_var, n+1)

        for dep in deps:
            getattr(model, dep)

        return retval

    def _assert_on_second(self, model, state_var='_has_run', retval=42):
        has_run = getattr(self, state_var)
        assert 0 == has_run, "Not supposed to run a second time"
        setattr(self, state_var, 1)
        return retval

    def _assert_on_first(self, model):
        assert False, "Not supposed to run ever"

    def test_basic_cache(self):
        self._state_a = 0

        f_A = self._wrap_func(self._assert_on_second,
                              state_var='_state_a',
                              retval='A')

        m = pylink.DAGModel(A=f_A)
        e = m.enum

        m.A
        assert 1 == self._state_a, "A was not calculated"

        m.A
        assert 1 == self._state_a, "A was recalculated"

    def test_selective_cache_clear(self):
        """Ensures that a non-dependent cached-item is not re-calculated.

        A: Tracking calculator
        B: Tracking calculator
        C: Assert second time

        Dependent pathway:
        A <-- B

        Independent pathway:
        C

        Calculate B
        Calculate C

        Ensure:
         * A was calculated
         * B was calculated
         * C was calculated

        Override A
        Calculate B

        Ensure:
         * A was served from the override value and was NOT recalculated
         * B was recalculated
         * C was NOT recalculated
        """

        self._state_a = 0
        self._state_b = 0
        self._state_c = 0

        f_A = self._wrap_func(self._tracking_calculator,
                              state_var='_state_a',
                              retval='A')
        f_B = self._wrap_func(self._tracking_calculator,
                              state_var='_state_b',
                              retval='B',
                              deps=['A'])
        f_C = self._wrap_func(self._assert_on_second,
                              state_var='_state_c',
                              retval='C')

        m = pylink.DAGModel(A=f_A, B=f_B, C=f_C)
        e = m.enum

        m.B
        assert 1 == self._state_a, "A was not calculated"
        assert 1 == self._state_b, "B was not calculated"

        m.C
        assert 1 == self._state_c, "C was not calculated"

        m.override(e.A, "A'")

        m.B
        assert 1 == self._state_a, "A was recalculated"
        assert 2 == self._state_b, "B was not recalculated"

        m.C
        assert 1 == self._state_c, "C was recalculated"
