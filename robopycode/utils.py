# -*- coding: utf-8 -*-
import math

from robogame_engine.geometry import Vector, Point, normalise_angle, get_arctan
from robogame_engine.theme import theme


def in_radar_fork(obj, target):
    """
        Is target in radar beam?
    """
    _half_tank_radar_angle = theme.TANK_RADAR_ANGLE // 2
    _radar_point_back_distance = math.sin(_half_tank_radar_angle / 180 * math.pi) * obj.radius

    point_back_vector = Vector.from_direction(obj.vector.direction + 180, _radar_point_back_distance)
    point_back = Point(obj.coord.x, obj.coord.y)
    point_back += point_back_vector

    dx = target.coord.x - point_back.x
    dy = target.coord.y - point_back.y

    left_radar_angle = normalise_angle(obj.vector.direction + _half_tank_radar_angle)
    right_radar_angle = normalise_angle(obj.vector.direction - _half_tank_radar_angle)

    target_direction = get_arctan(dy, dx)
    obj.debug("course {} dx {} dy {}}", obj.vector.direction, dx, dy)
    obj.debug("left_angle {} right_angle {} target_direction {}",
              left_radar_angle, right_radar_angle, target_direction)

    if right_radar_angle < target_direction < left_radar_angle:
        obj.debug("in radar beam")
        return True
    if 0 + theme.TANK_RADAR_ANGLE > left_radar_angle and \
                    right_radar_angle > 360 - theme.TANK_RADAR_ANGLE:
        obj.debug("radar beam near zero")
        if target_direction < left_radar_angle:
            obj.debug("target_direction < left_radar_angle")
            return True
        if target_direction > right_radar_angle:
            obj.debug("target_direction > right_radar_angle")
            return True

    return False

