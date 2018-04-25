# -*- coding: utf-8 -*-

from robogame_engine.geometry import Point
from robogame_engine.scene import random_point
from robogame_engine.theme import theme
from robopycode.core import Battlezone

from robopycode.tank import Tank, Target


class SimpleTank(Tank):

    def turn_around(self):
        self.debug("turn_around")
        self.turn_to(self.direction + 180)

    def to_search(self):
        self.debug("to_search")
        self._state = 'search'
        self.target = None
        point = random_point()
        self.move_at(point)

    def to_hunt(self, target_candidate):
        self.debug("to_hunt")
        self.target = target_candidate
        self._state = 'hunt'
        if self.distance_to(self.target) > 100:
            self.move_at(self.target)
            self.debug("move_at {target}", target=self.target)
        else:
            self.turn_to(self.target)
            self.debug("turn_to {target}", target=self.target)
        self.fire()

    def make_decision(self, objects=None):
        """
            Принять решение, охотиться ли за обьектами
        """
        self.debug("make_decision {objects}", objects=objects)
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

    def on_stop_at_target(self, obj):
        self.to_search()

    def on_gun_reloaded(self):
        if self._state == 'hunt':
            try:
                if self.target.armor > 0:
                    self.fire()
            except AttributeError:
                self.to_search()

    def on_target_destroyed(self):
        self.to_search()

    def on_collide_with(self, obj):
        self.debug("collided_with, state {_state}")
        self.make_decision(objects=[obj])

    def on_radar_detect(self, objects):
        for obj in objects:
            self.debug("in radar obj with armor {}".format(obj.armor))
        self.debug("in_tank_radar_range state {_state} target {target}")
        self.make_decision(objects)


class CooperativeTank(Tank):

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
            self.turn_to(self.direction + 90)
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


if __name__ == '__main__':
    battlezone = Battlezone(
        name="Battlezone: To the dust!",
        # field=(800, 600),
        theme_mod_path='robopycode.themes.default',
        speed=5,
    )
    team_size = 10

    deploy1 = Point(theme.FIELD_WIDTH - 100, 100)
    army_1 = [SimpleTank(pos=deploy1) for i in range(team_size)]

    deploy2 = Point(100, theme.FIELD_HEIGHT - 100)
    army_2 = [CooperativeTank(pos=deploy2) for i in range(team_size)]

    deploy3 = Point(100, 100)
    targets_count = 5
    targets = [Target(pos=random_point()) for i in range(targets_count)]
    # targets += [Target(pos=random_point(), auto_fire=True) for i in range(targets_count)]
    #
    # second_pos = Point(theme.FIELD_WIDTH - 20, theme.FIELD_HEIGHT - 20)
    # targets += [
    #     StaticTarget(pos=Point(20, 20), direction=90),
    #     StaticTarget(pos=second_pos, direction=-90, auto_fire=True)
    # ]

    battlezone.go()
