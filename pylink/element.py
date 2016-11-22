#!/usr/bin/python


class Element(object):

    def __init__(self, gain_db, noise_figure_db, name, **kwargs):
        self.gain_db = gain_db
        self.noise_figure_db = noise_figure_db
        self.name = name
        self.meta = kwargs
