#!/usr/bin/env python
# -*- coding: utf-8 -*-

import constants
from engine import Scene
from objects import Tank, Target, StaticTarget
from geometry import Vector, Point
from common import random_point
from robogame_engine import theme


class SimpleTank(Tank):
    _img_file_name = 'tank_blue.png'



class CooperativeTank(Tank):
    """Танк. Может ездить по экрану."""
    _img_file_name = 'tank_green.png'


class Battlezone(Scene):
    check_collisions = False
    _FLOWER_JITTER = 0.7
    _HONEY_SPEED_FACTOR = 0.02
    __beehives = []

    def prepare(self):
        self._objects_holder = self


if __name__ == '__main__':
    battlezone = Battlezone(
        name="Battlezone: To the dust!",
        # field=(800, 600),
        theme_mod_path='themes.default',
    )

    count = 10
    deploy1 = Point(theme.FIELD_WIDTH - 100, 100)
    army_1 = [SimpleTank(pos=deploy1) for i in range(5)]

    deploy2 = Point(100, theme.FIELD_HEIGHT - 100)
    army_2 = [CooperativeTank(pos=deploy2) for i in range(5)]

    deploy3 = Point(100, 100)
    targets = [Target(pos=deploy3) for i in range(4)]
    targets += [Target(pos=deploy3, auto_fire=True) for i in range(4)]

    second_pos = (theme.FIELD_WIDTH - 20, theme.FIELD_HEIGHT - 20)
    targets += [
        StaticTarget(pos=(20, 20), angle=90),
        StaticTarget(pos=second_pos, angle=-90, auto_fire=True)
    ]

    battlezone.go()
