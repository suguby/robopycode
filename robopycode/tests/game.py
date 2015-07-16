# -*- coding: utf-8 -*-

from robogame_engine import Scene
from robogame_engine.geometry import Point, Vector
from robogame_engine.scene import random_point
from robogame_engine.theme import theme

from robopycode.tank import Tank, StaticTarget, Target


class SimpleTank(Tank):

    def turn_around(self):
        self.turn_to(self.course + 180)

    def run_away(self, obj):
        to_obj_vector = Vector(self, obj)
        self.move(to_obj_vector.angle + 180, speed=5)

    def to_search(self):
        self._state = 'search'
        self.target = None
        self.move_at(random_point())

    def to_hunt(self, target_candidate):
        self.target = target_candidate
        self._state = 'hunt'
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
        if self._state == 'search':
            if target_candidate:
                self.to_hunt(target_candidate)
        elif self._state == 'hunt':
            if target_candidate:
                self.to_hunt(target_candidate)
            else:
                if self.target:
                    self.to_hunt(self.target)
                else:
                    self.to_search()

    def on_born(self):
        self.to_search()

    def on_stop(self):
        self.to_search()

    def stopped_at_target(self):
        self.to_search()

    def on_gun_reloaded(self):
        if self._state == 'hunt':
            if self.target and self.target.armor > 0:
                self.fire()
            else:
                self.to_search()

    def on_target_destroyed(self):
        self.to_search()

    def on_collided_with(self, obj):
        self.debug("collided_with, state {_state}")
        if self._state == 'search':
            self.make_decision(objects=[obj])

    def on_radar_detect(self, objects):
        for obj in objects:
            self.debug("in radar obj with armor {}".format(obj.armor))
        self.debug("in_tank_radar_range state {_state} target {target}")
        self.make_decision(objects)

    def hearbeat(self):
        self.debug("hearbeat")


class CooperativeTank(Tank):
    """Танк. Может ездить по экрану."""
    _sprite_filename = 'tank_green.png'
    all_tanks = []
    target = None
    _min_armor = 50
    _min_distance_to_target = 150
    _state = 'at_home'

    def on_born(self):
        self.__class__.all_tanks.append(self)
        self.retreat_point = Point(100, theme.FIELD_HEIGHT - 100)
        self.determine_state()

    def on_stop(self):
        self.determine_state()

    def on_stop_at_target(self, target):
        self.determine_state()

    def on_gun_reloaded(self):
        self.determine_state()

    def on_hitted(self):
        self.determine_state()

    def hearbeat(self):
        self.debug("hearbeat")
        self.determine_state()

    def on_radar_detect(self, objects):
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

    def follow_target(self, with_move=True):
        if self.is_near_target():
            self.debug("near_target - turned to {target}")
            self.turn_to(self.target)
            self.fire()
            self._state = 'hunt'
        elif with_move:
            if self.target:
                self.debug("target far away - move to")
                self.move_at(self.target)
                self._state = 'folow_target'
            else:
                self.debug("no target - random")
                self._state = 'search'
                self.move_at(random_point())
        else:
            self.debug("target far away and no move - dancing")
            self.turn_to(self.course + 90)
            self._state = 'search'

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



class Battlezone(Scene):
    check_collisions = True
    _FLOWER_JITTER = 0.7
    _HONEY_SPEED_FACTOR = 0.02
    __beehives = []

    def prepare(self):
        self._objects_holder = self

if __name__ == '__main__':
    battlezone = Battlezone(
        name="Battlezone: To the dust!",
        # field=(800, 600),
        theme_mod_path='robopycode.themes.default',
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
        StaticTarget(pos=(20, 20), direction=90),
        StaticTarget(pos=second_pos, direction=-90, auto_fire=True)
    ]

    battlezone.go()
