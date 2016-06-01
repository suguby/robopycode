# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-

import os

DEBUG = False

BACKGROUND_COLOR = (85, 107, 47)
PICTURES_PATH = os.path.join(os.path.dirname(__file__))

FIELD_WIDTH = 1200
FIELD_HEIGHT = 600

METER_1_COLOR = (0, 255, 70)
METER_2_COLOR = (232, 129, 31)

# See robogame_engine.constants

TANK_MAX_ARMOR = 100
TANK_SPEED = 5
TANK_TURN_SPEED = 5
TANK_ARMOR_RENEWAL_RATE = 0.035
TANK_GUN_HEAT_AFTER_FIRE = 80
TANK_RADAR_RANGE = 200
TANK_RADAR_ANGLE = 60

SHOT_POWER = 10
SHOT_SPEED = 20
SHOT_LIFE = 60  # in game ticks

# LOGLEVEL = 'INFO'
