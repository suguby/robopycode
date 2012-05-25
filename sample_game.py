#!/usr/bin/env python
# -*- coding: utf-8 -*-

import constants
from engine import Scene
from objects import Tank, Target, StaticTarget
from geometry import Vector, Point
from common import random_point


class SimpleTank(Tank):
    _img_file_name = 'tank_blue.png'

    def turn_around(self):
        self.turn_to(self.course + 180)

    def run_away(self, obj):
        to_obj_vector = Vector(self, obj)
        self.move(to_obj_vector.angle + 180, speed=5)

    def to_search(self):
        self.state = 'search'
        self.target = None
        self.move_at(random_point())

    def to_hunt(self, target_candidate):
        self.target = target_candidate
        self.state = 'hunt'
        if self.distance_to(self.target) > 100:
            self.move_at(self.target)
        else:
            self.turn_to(self.target)
        self.fire()

    def make_decision(self, objects=None):
        """
            Принять решение, охотиться ли за обьектами
        """
        target_candidate = None
        if self.target:
            distance_to_target = self.distance_to(self.target)
        else:
            distance_to_target = 100000
        for obj in objects:
            if not isinstance(obj, self.__class__):
                distance_to_candidate = self.distance_to(obj)
                if distance_to_candidate < distance_to_target:
                    target_candidate = obj
                    distance_to_target = distance_to_candidate
        if self.state == 'search':
            if target_candidate:
                self.to_hunt(target_candidate)
        elif self.state == 'hunt':
            if target_candidate:
                self.to_hunt(target_candidate)
            else:
                if self.target:
                    self.to_hunt(self.target)
                else:
                    self.to_search()

    def born(self):
        self.to_search()

    def stopped(self):
        self.to_search()

    def stopped_at_target(self):
        self.to_search()

    def gun_reloaded(self):
        if self.state == 'hunt':
            if self.target and self.target.armor > 0:
                self.fire()
            else:
                self.to_search()

    def target_destroyed(self):
        self.to_search()

    def collided_with(self, obj):
        self.debug("collided_with state %s", self.state)
        if self.state == 'search':
            self.make_decision(objects=[obj])

    def in_tank_radar_range(self, objects):
        for obj in objects:
            self.debug("in radar obj with armor %s", obj.armor)
        self.debug("in_tank_radar_range state %s target",
            self.state, self.target)
        self.make_decision(objects)

    def hearbeat(self):
        self.debug("hearbeat")


class CooperativeTank(Tank):
    """Танк. Может ездить по экрану."""
    _img_file_name = 'tank_green.png'
    all_tanks = []
    target = None
    _min_armor = 50
    _min_distance_to_target = 150
    state = 'at_home'
    retreat_point = Point(100, constants.field_height - 100)

    def born(self):
        """ событие: рождение """
        self.__class__.all_tanks.append(self)
        self.determine_state()

    def stopped(self):
        """событие: остановка"""
        self.determine_state()

    def stopped_at_target_point(self, point):
        """событие: остановка у цели"""
        self.determine_state()

    def gun_reloaded(self):
        self.determine_state()

    def hitted(self):
        self.determine_state()

    def hearbeat(self):
        self.determine_state()

    def in_tank_radar_range(self, objects):
        self.determine_target(objects)
        self.determine_state()

    def determine_target(self, objects):
        self.target = None
        friends, enemies = [], []
        for obj in objects:
            if self.is_friend(obj):
                friends.append(obj)
            else:
                enemies.append(obj)
        if enemies:
            self.target = self._get_nearest_obj(enemies)
            nearest_friend = self._get_nearest_obj(friends)
            if nearest_friend and self.distance_to(nearest_friend) < self.distance_to(self.target):
                self.target = None

    def follow_target(self, with_move = True):
        if self.is_near_target():
            self.debug("near_target - turned to %s" % self.target)
            self.turn_to(self.target)
            self.fire()
            self.state = 'hunt'
        elif with_move:
            if self.target:
                self.debug("target far away - move to")
                self.move_at(self.target)
                self.state = 'folow_target'
            else:
                self.debug("no target - random")
                self.state = 'search'
                self.move_at(random_point())
        else:
            self.debug("target far away and no move - dancing")
            self.turn_to(self.course + 90)
            self.state = 'search'

    def is_at_home(self):
        return self.distance_to(self.retreat_point) < 50 and self.armor < 90

    def is_near_target(self):
        return (self.target
                and self.target.armor > 0
                and self.distance_to(self.target) < self._min_distance_to_target
            )

    def is_friend(self, obj):
        return isinstance(obj, self.__class__)

    def is_need_retreat(self):
        return self.armor < self._min_armor

    def determine_state(self):
        if self.is_at_home():
            self.debug("at_home")
            self.follow_target(with_move=False)
        elif self.is_need_retreat():
            self.debug("need_retreat")
            self.target = None
            self.move_at(self.retreat_point)
        elif self.target:
            self.debug("i alive and have target")
            self.follow_target()
        else:
            self.debug("check friends targets")
            self.target = None
            for tank in self.__class__.all_tanks:
                if tank is self:
                    continue
                if tank.target and tank.target.armor > 0:
                    self.target = tank.target
                    break
            self.follow_target()

    def _get_nearest_obj(self, objects):
        if objects:
            nearest_obj = objects[0]
            for obj in objects[1:]:
                if self.distance_to(obj) < self.distance_to(nearest_obj):
                    nearest_obj = obj
            return nearest_obj
        return None


scene = Scene('Tanks world')

army_1 = [SimpleTank() for i in range(5)]

army_2 = [CooperativeTank() for i in range(5)]

targets = [Target() for i in range(4)]
targets += [Target(auto_fire=True) for i in range(4)]

second_pos = (constants.field_width - 20, constants.field_height - 20)
targets += [
    StaticTarget(pos=(20,20), angle=90),
    StaticTarget(pos=second_pos, angle=-90, auto_fire=True)
]

scene.go()
