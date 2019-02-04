#!/usr/bin/env python

import pylink
import pytest

from testutils import model


class TestModel(object):

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

    def test_loop_induction(self):
        """Ensures that a loop-inducing calculation can be made

        A -> B -> C -> D -> B

        C is a member of set {1, 2, 3}
        """

        def f_A(m):
            return m.B

        def f_B(m):
            return m.C
        
        def f_C(m):
            e = m.enum

            retval = -1

            for v in m.C_opt:
                m.override(e.C, v)
                b = m.cached_calculate(e.B, clear_stack=True)
                m.revert(e.C)
                retval = max(retval, b)

            return retval
        
        def f_D(m):
            return m.B

        def f_C_opt(m):
            return [1, 2, 3]

        m = pylink.DAGModel(A=f_A, B=f_B, C=f_C, D=f_D, C_opt=f_C_opt)

        assert m.A == 3

    def test_all_nodes(self, model):
        for node in model.nodes():
            model.cached_calculate(node)

    def test_static_revert_error(self):
        """Ensure a revert of a static node throws an error.
        """

        m = pylink.DAGModel(A=42)
        e = m.enum

        assert m.A == 42
        m.override(e.A, 41)
        assert m.A == 41
        with pytest.raises(AttributeError):
            m.revert(e.A)

    def test_basic_override(self):

        m = pylink.DAGModel(A=42)
        e = m.enum

        assert m.A == 42
        m.override(e.A, 41)
        assert m.A == 41

    def test_is_calculated_node(self, model):
        e = model.enum
        assert model.is_calculated_node(e.link_margin_db)
        assert not model.is_calculated_node(e.rx_antenna_noise_temp_k)

    def test_is_static_node(self, model):
        e = model.enum
        assert model.is_static_node(e.rx_antenna_noise_temp_k)
        assert not model.is_static_node(e.link_margin_db)

    def test_is_overridden(self, model):
        e = model.enum

        # static nodes cannot be overridden, so try one first
        assert model.is_static_node(e.rx_antenna_noise_temp_k)
        assert not model.is_overridden(e.rx_antenna_noise_temp_k)

        # now try a calculated node
        assert model.is_calculated_node(e.link_margin_db)
        assert not model.is_overridden(e.link_margin_db)
        model.override(e.link_margin_db, 1)
        assert model.is_overridden(e.link_margin_db)
        model.revert(e.link_margin_db)
        assert not model.is_overridden(e.link_margin_db)

    def test_solve_for(self, model):
        m = model
        e = m.enum

        # Basic operation - make sure it doesn't die
        tmp = m.solve_for(e.rx_antenna_noise_temp_k,
                          e.link_margin_db,
                          0.125,
                          300, 5000, 10,
                          rounds=1)

        # Basic operation - make sure it doesn't die on 10 rounds
        tmp = m.solve_for(e.rx_antenna_noise_temp_k,
                          e.link_margin_db,
                          0.125,
                          300, 5000, 10,
                          rounds=10)

        # Should error-out on invalid input: same input and output
        with pytest.raises(AttributeError):
            tmp = m.solve_for(e.link_margin_db,
                              e.link_margin_db,
                              0.125,
                              300, 5000, 10,
                              rounds=10)

        # Should error-out on invalid input: static output variable
        with pytest.raises(AttributeError):
            tmp = m.solve_for(e.link_margin_db,
                              e.rx_antenna_noise_temp_k,
                              0.125,
                              300, 5000, 10,
                              rounds=10)

        # Should error-out on invalid input: 0 step size
        with pytest.raises(AttributeError):
            tmp = m.solve_for(e.link_margin_db,
                              e.rx_antenna_noise_temp_k,
                              0.125,
                              300, 5000, 0,
                              rounds=10)

        # Should error-out on invalid input: negative rounds
        with pytest.raises(AttributeError):
            tmp = m.solve_for(e.link_margin_db,
                              e.rx_antenna_noise_temp_k,
                              0.125,
                              300, 5000, 0,
                              rounds=-1)

        # Should error-out on invalid input: non-integer rounds
        with pytest.raises(AttributeError):
            tmp = m.solve_for(e.link_margin_db,
                              e.rx_antenna_noise_temp_k,
                              0.125,
                              300, 5000, 0,
                              rounds=1.0)

        # Basic operation: proper value
        def __round(ans, order):
            return round(ans * 10**order)/10**order

        model.override(e.rx_ebn0_db, 10.0)
        model.override(e.required_ebn0_db, 2.0)
        target = 0.1257354
        ans = 2.0 + target

        for i in range(10):
            tmp = m.solve_for(e.rx_ebn0_db,
                              e.link_margin_db, target,
                              0.0, 10.0, 1.0,
                              rounds=i+1)
            assert abs(__round(ans, i) - tmp) < 1e-6
