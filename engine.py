#!/usr/bin/env python
# -*- coding: utf-8 -*-

import user_interface
import geometry
import objects
import common
import math
import constants
import events


class Scene:
    """
        Game scene. Container for all game objects.
    """

    def __init__(self, name):
        self.grounds = []
        self.shots = []
        self.exploisons = []

        objects.Shot.container = self.shots
        objects.Explosion.container = self.exploisons
        objects.Tank.container = self.grounds

        self.ui = user_interface.UserInterface(name)
        self.hold_state = False  # режим пошаговой отладки
        self._step = 0

    def _game_step(self):
        """
            Proceed objects states, collision detection, hits
            and radars discovering
        """
        for obj in self.grounds + self.shots:
            obj._distance_cache = {}
        for obj in self.grounds:
            obj._radar_detected_objs = []
            obj._detected_by = []
        searched_left_ids = []
        for left in self.grounds[:]:
            #~ searched_left_ids.append(left._id)
            left.debug(">>> start proceed at scene step")
            left.debug(str(left))
            for right in self.grounds[:]:
                if (right._id == left._id) or (right._id in searched_left_ids):
                    continue
                distance = left.distance_to(right)
                # коллизии
                overlap_distance = int(left.radius + right.radius - distance)
                if overlap_distance > 1:
                    # могут пересекаться одним пикселем
                    step_back_vector = geometry.Vector(right,
                                                       left,
                                                       overlap_distance // 2)
                    left.debug('step_back_vector %s', step_back_vector)
                    left.coord.add(step_back_vector)
                    right.coord.add(-step_back_vector)
                    left._events.put(events.EventCollide(right))
                    right._events.put(events.EventCollide(left))
                # радары
                if distance < constants.tank_radar_range:
                    left.debug("distance < constants.tank_radar_range for %s",
                               right._id)
                    if _in_radar_fork(left, right):
                        left.debug("see %s", right._id)
                        if right.armor > 0:
                            left._radar_detected_objs.append(right)
                            right._detected_by.append(left)
            # попадания (список летяших снарядов может уменьшаться)
            for shot in self.shots[:]:
                if shot.owner and shot.owner == left:
                    continue
                if _collide_circle(shot, left):
                    left.hit(shot)
                    shot.detonate_at(left)
                    self.shots.remove(shot)
        # после главного цикла - евенты могут меняться
        for obj in self.grounds:
            if obj._radar_detected_objs:
                radar_event = events.EventRadarRange(obj._radar_detected_objs)
                obj._events.put(radar_event)
            obj._proceed_events()
            obj._game_step()

        for obj in self.shots + self.exploisons:
            obj._game_step()

    def go(self):
        """
            Main game cycle - the game begin!
        """
        while True:

            # получение состояния клавы и мыши
            self.ui.get_keyboard_and_mouse_state()
            if self.ui.the_end:
                break

            # выделение обьектов мышкой
            if self.ui.mouse_buttons[0] and not self.mouse_buttons[0]:
                # mouse down
                for obj in self.grounds:
                    if obj.rect.collidepoint(self.ui.mouse_pos):
                        # координаты экранные
                        obj._selected = not obj._selected
                        obj.debug('select %s', obj)
#                        self.selected = obj
                    elif not common._debug:
                        # возможно выделение множества танков
                        # только на режиме отладки
                        obj._selected = False

            self.mouse_buttons = self.ui.mouse_buttons

            # переключение режима отладки
            if self.ui.switch_debug:
                if common._debug:  # были в режиме отладки
                    self.hold_state = False
                    self.ui.clear_screen()
                else:
                    self.hold_state = True
                common._debug = not common._debug
                self.ui.debug = common._debug

            # шаг игры, если надо
            if not self.hold_state or self.ui.one_step:
                self._step += 1
                self._game_step()
                if common._debug:
                    common.log.debug('=' * 20, self._step, '=' * 10)

            # отрисовка
            self.ui.draw()

        print 'Thank for playing robopycode! See you in the future :)'

############################################################ утилиты ##########


def _collide_circle(left, right):
    """
        Detect collision by radius of objects
    """
    return left.distance_to(right) <= left.radius + right.radius


def _overlapped(left, right):
    """
        Is two objects overlapped
    """
    return int((left.radius + right.radius) - left.distance_to(right))


_half_tank_radar_angle = constants.tank_radar_angle // 2
_radar_point_back_distance = math.sin(_half_tank_radar_angle / 180 * math.pi) \
                                * objects.Tank.radius


def _in_radar_fork(obj, target):
    """
        Is target in radar beam?
    """
    point_back_vector = geometry.Vector(obj.course + 180,
                                        _radar_point_back_distance)
    point_back = geometry.Point(obj.coord)
    point_back.add(point_back_vector)

    dx = target.coord.x - point_back.x
    dy = target.coord.y - point_back.y

    left_radar_angle = geometry.normalise_angle(obj.course
                                                  + _half_tank_radar_angle)
    right_radar_angle = geometry.normalise_angle(obj.course
                                                   - _half_tank_radar_angle)

    target_direction = geometry.get_arctan(dy, dx)
    obj.debug("course %s dx %s dy %s", obj.course, dx, dy)
    obj.debug("left_angle %s right_angle %s target_direction %s",
              left_radar_angle, right_radar_angle, target_direction)

    if right_radar_angle < target_direction < left_radar_angle:
        obj.debug("in radar beam")
        return True
    if 0 + constants.tank_radar_angle > left_radar_angle and \
       right_radar_angle > 360 - constants.tank_radar_angle:
        obj.debug("radar beam near zero")
        if target_direction < left_radar_angle:
            obj.debug("target_direction < left_radar_angle")
            return True
        if target_direction > right_radar_angle:
            obj.debug("target_direction > right_radar_angle")
            return True

    return False
