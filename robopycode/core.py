# -*- coding: utf-8 -*-
from robogame_engine import GameObject, Scene
from robogame_engine.geometry import Point, Vector
from robogame_engine.theme import theme
from robopycode.events import EventGunReloaded, EventRadarDetect
from robopycode.utils import in_radar_fork


class Gun:
    states = ['reloading', 'loaded']

    def __init__(self, owner):
        self.owner = owner
        self.heat = 8
        self._state = 'reloading'

    def game_step(self):
        """
            Internal function
        """
        if self._state == 'reloading':
            self.heat -= 1
            if not self.heat:
                # перезарядка только что кончилась
                self.owner._events.put(EventGunReloaded())
                self._state = 'loaded'

    def fire(self):
        """
            Fire from gun
        """
        if self._state == 'loaded':
            start_point = Point(
                self.owner.coord.x,
                self.owner.coord.y,
            ) + Vector.from_direction(
                direction=self.owner.direction,
                module=self.owner.radius // 2 + 12
            )
            shot = Shot(pos=start_point, direction=self.owner.direction, owner=self.owner)
            self.heat = theme.TANK_GUN_HEAT_AFTER_FIRE
            self._state = 'reloading'
            return shot


class Shot(GameObject):
    """
        The shell. Flies in a straight until it hits the target.
    """
    layer = 1
    radius = 4
    selectable = False

    def __init__(self, pos, direction, owner):
        """
            Start a shell from a specified point in the direction of the
        """
        GameObject.__init__(self, pos, direction)
        self.owner = owner
        target = self.owner.coord + Vector.from_direction(direction, module=50000)  # far away...
        self.move_at(target=target, speed=theme.SHOT_SPEED)
        self.life = theme.SHOT_LIFE
        self.power = theme.SHOT_POWER

    def on_collide_with(self, obj):
        """
            Event: contact with our tank shell
        """
        if obj is self.owner:
            return
        from robopycode.tank import Tank
        if isinstance(obj, Tank):
            obj.hit(shot=self)
            self.detonate_at(obj)

    def detonate_at(self, obj):
        """
            Explosion!
        """
        SmallExplosion(self.coord, obj)  # взрыв на месте снаряда
        self._scene.remove_object(self)
        if self.owner:
            self.owner.shot = None
            self.owner = None

    def game_step(self):
        super(Shot, self).game_step()
        self.debug('{coord}')
        self.life -= 1
        if not self.life or not self.is_moving:
            if self.owner:
                self.owner.shot = None
            self._scene.remove_object(self)


class Explosion(GameObject):
    """
        The explosion of the tank.
    """
    layer = 0
    radius = 0  # collision detect
    defaultlife = 12
    animcycle = 3
    selectable = False  # обьект нельзя выделить мышкой
    animated = True  # надо анимировать обьект TODO сделать анимацию в гифке

    def __init__(self, explosion_coord, hitted_obj):
        super(Explosion, self).__init__(pos=explosion_coord)
        self.vector = Vector.from_points(hitted_obj.coord, explosion_coord)
        self.vector.rotate(-hitted_obj.direction)  # смещение при отображении
        self.owner = hitted_obj
        self.owner.explosion = self
        self.owner._update_explosion()
        self.life = self.defaultlife

    def game_step(self):
        super(Explosion, self).game_step()
        self.life -= 1
#        self.image = self.images[self.life // self.animcycle % 2]
        if self.life <= 0:
            self._scene.remove_object(self)
            self.owner.explosion = None
            self.owner = None


class SmallExplosion(Explosion):
    """
        The explosion of the shell.
    """


class Battlezone(Scene):
    check_collisions = True

    def prepare(self):
        self._objects_holder = self

    def game_step(self):
        super(Battlezone, self).game_step()
        from robopycode.tank import Tank
        all_tanks = self.get_objects_by_type(Tank)
        for tank in all_tanks:
            tank.radar_detected = []
        tanks = all_tanks[:]
        while True:
            left = tanks.pop()
            if not tanks:
                break
            for right in tanks:
                distance = left.distance_to(right)
                if distance > theme.TANK_RADAR_RANGE + left.radius:
                    continue
                if left.has_radar and in_radar_fork(left, right):
                    left.radar_detected.append(right)
                if right.has_radar and in_radar_fork(right, left):
                    right.radar_detected.append(left)
        for tank in all_tanks:
            if tank.radar_detected:
                event = EventRadarDetect(tank.radar_detected)
                tank.add_event(event)

