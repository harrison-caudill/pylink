#!/usr/bin/python

import math
import numpy as np


class Variate(object):

    def __init__(self, init_value, **meta):
        self._value = init_value
        self.meta = meta
        self.value = init_value
        self.history = [self.value]
        self._post_model_hook = None

    def model_init(self, model):
        """Registers the DAGModel.

        This is done so that things like node numbers can be cached.
        The Model is expected to be complete, and all the variates
        registered, though the ordering of these calls is undefined.
        """
        if self._post_model_hook:
            self._post_model_hook(model)

    def evolve(self, model):
        """Updates to a new value of the variate.
        """
        retval = self._evolve(model)
        self.history.append(retval)
        self.value = retval
        return retval


class GeneralVariate(Variate):

    def __init__(self, init_value, evolve, **meta):
        super(GeneralVariate, self).__init__(init_value, **meta)
        self.evolve_func = evolve

    def _evolve(self, model):
        return self.evolve_func(self, model, self.history)


class IndependentNormalVariate(Variate):

    def __init__(self, init_value, mu, sigma, **meta):
        self.mu = mu
        self.sigma = sigma
        super(IndependentNormalVariate, self).__init__(init_value, **meta)

    def _evolve(self, model):
        return model.random().normal(loc=self.mu, scale=self.sigma)


class MarkovVariate(Variate):

    def __init__(self, init_value, evolve, opt=None, **meta):
        super(MarkovVariate, self).__init__(init_value, **meta)
        self.evolve_func = evolve
        self.opt = opt

    def _evolve(self, model):
        return self.evolve_func(self.history, self.opt)


class IndependentCustomPMFVariate(Variate):

    def __init__(self, init_value, pmf, **meta):
        # at least 10 samples per bucket
        n = 10 * 1.0 / min(pmf)
        self.rand = numpy.zeros(n)
        j = 0
        for i in range(len(pmf)):
            for k in range(int(round(pmf[i] * n, 0))):
                self.rand[k] = i

        super(IndependentCustomPMFVariate, self).__init__(init_value, **meta)

    def _evolve(self, model):
        return model.random().choice(self.rand)


class IndependentBinomialVariate(Variate):

    def __init__(self, init_value, n, p, **meta):
        self.n = n
        self.p = p

        super(IndependentBinomialVariate, self).__init__(init_value, **meta)

    def _evolve(self, model):
        return model.random().binomial(self.n, self.p)


class DependentNormalVariate(Variate):

    def __init__(self, init_value, mu, sigma, **meta):
        self.mu = mu
        self.sigma = sigma
        super(DependentNormalVariate, self).__init__(init_value, **meta)
        self._post_model_hook = self.__post_model_hook

    def __post_model_hook(self, model):
        self.mu = model.node_num(self.mu)
        self.sigma = model.node_num(self.sigma)

    def _evolve(self, model):
        mu = model.cached_calculate(self.mu)
        sigma = model.cached_calculate(self.sigma)
        return model.random().normal(loc=mu, scale=sigma)
