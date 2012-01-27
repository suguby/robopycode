#!/usr/bin/env python
# -*- coding: utf-8 -*-

import engine
import objects
from common import random_point

class WadTank(objects.Tank):
    _img_file_name = 'tank_green.png'

    def turn_around(self):
        self.turn_to(self.course + 180)

    def run_away(self, obj):
        to_obj_vector = geometry.Vector(self, obj)
        self.move(to_obj_vector.angle + 180, speed = 5)

    def to_hunt(self, target_candidate):
        self.target = target_candidate
        self.state = 'hunt'
        if self.distance_to(self.target) > 100:
            self.move_at(self.target)
        else:
            self.turn_to(self.target)
        self.fire()

    def make_decision(self, objects=None):
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
                    self.state = 'search'
                    self.move_at(random_point())


    def born(self):
        self.state = 'search'
        self.target = None
        self.move_at(random_point())
    #        self.fire()

    def stopped(self):
        self.debug("state is %s", self.state)
        if self.state == 'search':
            self.move_at(random_point())
        elif self.state == 'hunt':
            self.state = 'search'
            self.target = None
            self.move_at(random_point())

    def stopped_at_target(self):
        if self.state == 'hunt':
            self.state = 'search'
        self.target = None
        self.move_at(random_point())

    def gun_reloaded(self):
        if self.state == 'hunt':
            if self.target and self.target.armor > 0:
                self.fire()
            else:
                self.state = 'search'
                self.target = None
                self.move_at(random_point())


    def target_destroyed(self):
        if self.state == 'hunt':
            self.state = 'search'
        self.target = None
        self.move_at(random_point())

    #    def hitted(self):
    #        self.debug("hitted state %s", self.state)
    #        if self.armor < 10:
    #            self.state = 'escape'
    #            self.move_at(random_point())
    #        if self.state == 'search':
    #        elif self.state == 'hunt':
    #            pass
    #        else:
    #            self.move_at(random_point())

    def collided_with(self, obj):
        self.debug("collided_with state %s", self.state)
        if self.state == 'search':
            self.state = 'hunt'
            self.target = obj
            self.move_at(obj)

    def in_tank_radar_range(self, objects):
        self.debug("in_tank_radar_range state %s target", self.state, self.target)
        self.make_decision(objects)

scene = engine.Scene('Tanks world')
tanks = [WadTank() for i in range(5)]
targets = [objects.Target() for i in range(10)]
scene.go()

