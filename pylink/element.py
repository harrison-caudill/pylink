#!/usr/bin/python


class Element(object):
    """RF Chain Element container object
    """

    def __init__(self, gain_db, noise_figure_db, name, **kwargs):
        """New RF Chain container

        Add any kwargs for any desired metadata for this object.  For
        example, the link to the datasheet, test report, or maybe its
        internal and/or external part numbers.
        """
        self.gain_db = float(gain_db)
        self.noise_figure_db = float(noise_figure_db)
        self.name = name
        self.meta = kwargs
