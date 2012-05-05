#!/usr/bin/env python
# -*- coding: utf-8 -*-

import constants
import random
import geometry

_debug = False


class Logger:
    """
        Logging game events
    """

    def debug(self, pattern, *args):
        to_console(pattern, *args)

log = Logger()


def to_console(pattern, *args):
    if _debug:
        pattern = str(pattern)
        try:
            print pattern % args
        except TypeError:
            print pattern, ' '.join([str(arg) for arg in args])


def random_point(object_radius=32):
    """
        Get random point inside screen
    """
    frame = object_radius // 2 + 1
    x = random.randint(frame, constants.field_width - frame)
    y = random.randint(frame, constants.field_height - frame)
    return geometry.Point(x, y)
