#!/usr/bin/python


class TaggedAttribute(object):

    def __init__(self, value, **kwargs):
        self.meta = kwargs
        self.value = value
