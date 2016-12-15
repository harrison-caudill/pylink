#!/usr/bin/python

import math
import numpy as np

class Variate(object):

    def __init__(self, initial_value, **meta):
        self.value = initial_value
        self.meta = meta
        self.history = [initial_value]

    def evolve(self, model):
        retval = self._evolve(model)
        self.history.append(retval)
        self.value = retval
        return retval


class GeneralVariate(Variate):

    def __init__(self, initial_value, evolve, **meta):
        super(GeneralVariate, self).__init__(initial_value, **meta)
        self.evolve_func = evolve

    def _evolve(self, model):
        return self.evolve_func(self, model, self.history)


class IndependentNormalVariate(Variate):

    def __init__(self, mu, sigma, **meta):
        self.mu = mu
        self.sigma = sigma
        init = np.random.normal(loc=self.mu, scale=self.sigma)
        super(IndependentNormalVariate, self).__init__(init, **meta)

    def _evolve(self, model):
        return np.random.normal(loc=self.mu, scale=self.sigma)


class MarkovVariate(Variate):

    def __init__(self, initial_value, evolve, opt=None, **meta):
        super(MarkovVariate, self).__init__(initial_value, **meta)
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

        init_val = np.random.choice(self.rand)
        super(IndependentCustomPMFVariate, self).__init__(init_val, **meta)

    def _evolve(self, model):
        return np.random.choice(self.rand)


class IndependentBinomialVariate(Variate):

    def __init__(self, n, p, **meta):
        self.n = n
        self.p = p

        init_val = np.random.binomial(self.n, self.p)
        super(IndependentBinomialVariate, self).__init__(init_val, **meta)

    def _evolve(self, model):
        return np.random.binomial(self.n, self.p)

class DependentNormalVariate(Variate):

    def __init__(self, initial_value, mu, sigma, **meta):
        self.mu = mu
        self.sigma = sigma
        super(DependentNormalVariate, self).__init__(initial_value, **meta)

    def _evolve(self, model):
        mu = model.cached_calculate(model.node_num(self.mu))
        sigma = model.cached_calculate(model.node_num(self.sigma))
        return np.random.normal(loc=mu, scale=sigma)
