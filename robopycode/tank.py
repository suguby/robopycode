# -*- coding: utf-8 -*-
from robogame_engine import GameObject
from robogame_engine.constants import ROTATE_TURNING
from robogame_engine.geometry import Point, Vector
from robogame_engine.scene import random_point
from robogame_engine.theme import theme
from robopycode.core import Gun, Explosion
from robopycode.events import EventTargetDestroyed, EventHit


class Tank(GameObject):
    """
        Tank. May ride on the screen.
    """
    radius = 32
    rotate_mode = ROTATE_TURNING
    selectable = True
    layer = 2

    _sprite_filename = 'tank_blue.png'

    def __init__(self, pos=None, direction=0):
        """
            create a tank in a specified point on the screen
        """
        super(Tank, self).__init__(pos=pos, direction=direction)
        self.gun = Gun(self)
        self._armor = float(theme.TANK_MAX_ARMOR)
        self.explosion = None

    @property
    def armor(self):
        return int(self._armor)

    @property
    def gun_heat(self):
        return self.gun.heat

    def game_step(self):
        if self._armor < theme.TANK_MAX_ARMOR:
            self._armor += theme.TANK_ARMOR_RENEWAL_RATE
        self.gun.game_step()
        super(Tank, self).game_step()
        self._update_explosion()

    def _update_explosion(self):
        """
            Renew exploison at the armor - it must moving with as
        """
        if self.explosion:
            self.explosion.coord = Point.from_point(self.coord)
            expl_shift = Vector.from_direction(
                direction=self.direction + self.explosion.vector.direction,
                module=self.explosion.vector.module
            )
            self.explosion.coord += expl_shift
            self.debug("after add explosion is {explosion}")

    def fire(self):
        """
            Make shot.
        """
        self.gun.fire()

    def detonate(self):
        """
            Suicide
        """
        self.stop()
        Explosion(self.coord, self)  # взрыв на нашем месте
        self._scene.remove_object(self)

    def hit(self, shot):
        """
            Contact with our tank shell
        """
        self._armor -= shot.power
        self.add_event(EventHit())
        if self._armor <= 0:
            if shot.owner:  # еще не был убит
                shot.owner.add_event(EventTargetDestroyed())
            self.detonate()

    # events processing
    def on_born(self):
        """
            Event: born
        """
        pass

    def on_gun_reloaded(self):
        """
            Event: the gun is ready to fire
        """
        pass

    def on_hitted(self):
        """
            Event: contact with our tank shell
        """
        pass

    def on_collide_with(self, obj):
        """
            Event: contact with our tank shell
        """
        pass

    def on_target_destroyed(self):
        """
            Event: our target destroed
        """
        pass

    def on_radar_detect(self, objects):
        """
            Event: contact with our tank shell
        """
        pass


class StaticTarget(Tank):
    """
        A static target
    """
    _sprite_filename = 'tank_red.png'
    selectable = False  # обьект нельзя выделить мышкой

    def __init__(self, pos=None, direction=0, auto_fire=False):
        Tank.__init__(self, pos=pos, direction=direction)
        self.auto_fire = auto_fire

    def on_gun_reloaded(self):
        if self.auto_fire:
            self.fire()


class Target(Tank):
    """
        A target
    """
    _sprite_filename = 'tank_red.png'
    _selectable = False  # обьект нельзя выделить мышкой

    def __init__(self, pos=None, direction=0, auto_fire=False):
        Tank.__init__(self, pos=pos, direction=direction)
        self.auto_fire = auto_fire

    def on_born(self):
        self.move_at(target=random_point())

    def on_stop(self):
        self.debug("stopped")
        self.move_at(target=random_point())

    def on_gun_reloaded(self):
        self.debug("gun_reloaded")
        if self.auto_fire:
            self.fire()

    def on_collide_with(self, obj):
        self.debug("on_collide_with {}".format(obj.id))
        self.move_at(target=random_point())
