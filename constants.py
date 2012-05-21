#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

# Scene constants
field_width = 640
field_height = 480

# Tank constants
tank_speed = 5
tank_turn_speed = 5
tank_max_armor = 100
tank_armor_renewal_rate = 0.035
tank_gun_heat_after_fire = 80
tank_radar_range = 200
tank_radar_angle = 40

# Shot constants
shot_power = 10
shot_speed = 10
shot_life = 60  # in game ticks

# GUI constants
background_color = (85, 107, 47)
resolution = (field_width, field_height)
data_path = os.path.join(os.path.dirname(__file__), 'data')

# engine constants
game_step_min_time = 0.015
