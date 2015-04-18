#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import math
from multiprocessing import Process, Pipe

from user_interface import UserInterface
import geometry
import objects
import common
import constants
import events


class ObjectState:
    """
        Hold game object state, useful for exchange between processes
    """
    params = (
        'id',
        'coord',
        'course',
        'armor',
        'gun_heat',
        '_revolvable',
        '_img_file_name',
        '_layer',
        '_selectable',
        '_animated'
        )

    def __init__(self, obj):
        for param in self.params:
            if hasattr(obj, param):
                val = getattr(obj, param)
                setattr(self, param, val)
        if hasattr(obj, '_detected_by'):
            self._detected_by = [
                detected_by_obj.id
                for detected_by_obj in obj._detected_by
            ]
        else:
            self._detected_by = []


def start_ui(name, child_conn):
    ui = UserInterface(name)
    ui.run(child_conn)


class Scene:
    """
        Game scene. Container for all game objects.
    """

    def __init__(self, name):
        self.grounds = []
        self.shots = []
        self.explosions = []

        objects.Shot.container = self.shots
        objects.Explosion.container = self.explosions
        objects.Tank.container = self.grounds

        self.hold_state = False  # режим пошаговой отладки
        self._step = 0
        self.name = name

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
            #~ searched_left_ids.append(left.id)
            left.debug(">>> start proceed at scene step")
            left.debug(str(left))
            for right in self.grounds[:]:
                if (right.id == left.id) or (right.id in searched_left_ids):
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
                               right.id)
                    if _in_radar_fork(left, right):
                        left.debug("see %s", right.id)
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
                    # self.shots.remove(shot)
        # после главного цикла - евенты могут меняться
        for obj in self.grounds:
            if obj._radar_detected_objs:
                radar_event = events.EventRadarRange(obj._radar_detected_objs)
                obj._events.put(radar_event)
            obj._proceed_events()
            obj._game_step()

        for obj in self.shots + self.explosions:
            obj._game_step()

        if common._debug:
            common.log.debug('=' * 20, self._step, '=' * 10)

    def go(self):
        """
            Main game cycle - the game begin!
        """
        self.parent_conn, child_conn = Pipe()
        self.ui = Process(target=start_ui, args=(self.name, child_conn,))
        self.ui.start()

        while True:
            cycle_begin = time.time()

            # проверяем, есть ли новое состояние UI на том конце трубы
            ui_state = None
            while self.parent_conn.poll(0):
                # состояний м.б. много, оставляем только последнее
                ui_state = self.parent_conn.recv()

            # состояние UI изменилось - отрабатываем
            if ui_state:
                if ui_state.the_end:
                    break

                for obj in self.grounds:
                    obj._selected = obj.id in ui_state.selected_ids

                # переключение режима отладки
                if ui_state.switch_debug:
                    if common._debug:  # были в режиме отладки
                        self.hold_state = False
                    else:
                        self.hold_state = True
                    common._debug = not common._debug

            # шаг игры, если надо
            if not self.hold_state or (ui_state and ui_state.one_step):
                self._step += 1
                self._game_step()
                # отсылаем новое состояние обьектов в UI
                objects_state = {}
                for obj in self.grounds + self.shots + self.explosions:
                    objects_state[obj.id] = ObjectState(obj)
                self.parent_conn.send(objects_state)

            # вычисляем остаток времени на сон
            cycle_time = time.time() - cycle_begin
            cycle_time_rest = constants.game_step_min_time - cycle_time
            if cycle_time_rest > 0:
                # о! есть время поспать... :)
                # print "sleep for %.6f" % cycle_time_rest
                time.sleep(cycle_time_rest)

        # ждем пока потомки помрут
        self.ui.join()

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
