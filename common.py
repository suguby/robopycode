#!/usr/bin/env python
# -*- coding: utf-8 -*-

import constants
import random
import geometry

_debug = False


class Logger:

    def debug(self, pattern, *args):
        if _debug:
            pattern = str(pattern)
            try:
                print pattern % args
            except:
                print pattern, ' '.join([str(arg) for arg in args])

log = Logger()

def random_point():
    return geometry.Point(random.randint(5, constants.field_width - 5),
                          random.randint(5, constants.field_height - 5))
