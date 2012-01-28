#!/usr/bin/env python
# -*- coding: utf-8 -*-

import engine
import objects
import geometry
from common import random_point


class WadTank(objects.Tank):
    _img_file_name = 'tank_blue.png'

    def turn_around(self):
        self.turn_to(self.course + 180)

    def run_away(self, obj):
        to_obj_vector = geometry.Vector(self, obj)
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
            if not isinstance(obj, WadTank):
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
        self.debug("in_tank_radar_range state %s target",
            self.state, self.target)
        self.make_decision(objects)

scene = engine.Scene('Tanks world')
tanks = [WadTank() for i in range(5)]
targets = [objects.Target() for i in range(10)]
scene.go()
