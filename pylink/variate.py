#!/usr/bin/python

import math
import numpy as np

class Variate(object):

    def __init__(self, init_value=None, **meta):
        self._value = init_value
        self.meta = meta
        self.history = []
        self.value = init_value

    def init_first_value(self, model):
        """Initializes the first value of the variate with full context.

        Some of the variates are dependent upon the model, which
        doesn't exist until after all of the variates are
        created/inititialized.  Doing it this way allows us to avoid a
        branch and a function call when referencing a variate's value.
        """
        if self.value is None:
            self.evolve(model)
        else:
            self.history.append(self.value)

    def evolve(self, model):
        """Updates to a new value of the variate.
        """
        retval = self._evolve(model)
        self.history.append(retval)
        self.value = retval
        return retval


class GeneralVariate(Variate):

    def __init__(self, evolve, init_value=None, **meta):
        super(GeneralVariate, self).__init__(init_value=init_value, **meta)
        self.evolve_func = evolve

    def _evolve(self, model):
        return self.evolve_func(self, model, self.history)


class IndependentNormalVariate(Variate):

    def __init__(self, mu, sigma, **meta):
        self.mu = mu
        self.sigma = sigma
        super(IndependentNormalVariate, self).__init__(**meta)

    def _evolve(self, model):
        return model.random().normal(loc=self.mu, scale=self.sigma)


class MarkovVariate(Variate):

    def __init__(self, evolve, opt=None, **meta):
        super(MarkovVariate, self).__init__(**meta)
        self.evolve_func = evolve
        self.opt = opt

    def _evolve(self, model):
        return self.evolve_func(self.history, self.opt)


class IndependentCustomPMFVariate(Variate):

    def __init__(self, pmf, **meta):
        # at least 10 samples per bucket
        n = 10 * 1.0 / min(pmf)
        self.rand = numpy.zeros(n)
        j = 0
        for i in range(len(pmf)):
            for k in range(int(round(pmf[i] * n, 0))):
                self.rand[k] = i

        super(IndependentCustomPMFVariate, self).__init__(**meta)

    def _evolve(self, model):
        return model.random().choice(self.rand)


class IndependentBinomialVariate(Variate):

    def __init__(self, n, p, **meta):
        self.n = n
        self.p = p

        super(IndependentBinomialVariate, self).__init__(**meta)

    def _evolve(self, model):
        return model.random().binomial(self.n, self.p)

class DependentNormalVariate(Variate):

    def __init__(self, mu, sigma, **meta):
        self.mu = mu
        self.sigma = sigma
        super(DependentNormalVariate, self).__init__(**meta)

    def _evolve(self, model):
        mu = model.cached_calculate(model.node_num(self.mu))
        sigma = model.cached_calculate(model.node_num(self.sigma))
        return model.random().normal(loc=mu, scale=sigma)
