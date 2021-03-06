#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Queue import Queue
from random import randint

from common import log, random_point
from constants import (tank_speed, tank_turn_speed,
                       field_width, field_height, tank_gun_heat_after_fire,
                       tank_max_armor, tank_armor_renewal_rate, shot_speed,
                       shot_life, shot_power)
from events import (EventHearbeat, EventStoppedAtTargetPoint, EventStopped,
                    EventGunReloaded, EventBorn, EventTargetDestroyed, EventHit)
from geometry import Point, Vector, normalise_angle
import user_interface


class GameObject():
    """
        Main game object
    """
    radius = 1
    _objects_count = 0
    states = ['stopped', 'turning', 'moving']
    container = None
    _animated = True

    def __init__(self, pos, revolvable=True, angle=None):
        self.coord = Point(pos)
        self.target_coord = Point(0, 0)

        if angle is None:
            angle = randint(0, 360)
        self.vector = Vector(angle, 0)
        self.course = self.vector.angle
        self.shot = False
        self._revolvable = revolvable
        self.load_value = 0
        self._distance_cache = {}
        self._events = Queue()
        self._selected = False
        self._state = 'stopped'
        self._need_moving = False

        # container - это список обьектов игры по типам,
        # инициализируется в Scene
        if self.container is None:
            raise Exception("You must create robopycode.engine.Scene"
                            " instance at first!")
        self.container.append(self)

        GameObject._objects_count += 1
        self.id = GameObject._objects_count
        self.debug('born %s', self)

        self._heartbeat_tics = 5

    def __str__(self):
        return 'obj(%s, %s %s cour=%.1f %s)' \
                % (self.id, self.coord, self.vector,
                   self.course, self._state)

    def __repr__(self):
        return str(self)

    def debug(self, pattern, *args):
        """
            Show debug information if DEBUG mode
        """
        if isinstance(self, Tank):
            if self._selected:
                log.debug('%s:%s' % (self.id, pattern), *args)
        else:
            log.debug('%s:%s:%s' % (self.__class__.__name__,
                                           self.id, pattern), *args)

    def _need_turning(self):
        return self._revolvable and int(self.course) != int(self.vector.angle)

    def turn_to(self, arg1):
        """
            Turn to the subject / in that direction
        """
        if isinstance(arg1, GameObject) or arg1.__class__ == Point:
            self.vector = Vector(self, arg1, 0)
        elif arg1.__class__ == int or arg1.__class__ == float:
            direction = arg1
            self.vector = Vector(direction, 0)
        else:
            raise Exception("use GameObject.turn_to(GameObject/Point "
                            "or Angle). Your pass %s" % arg1)
        self._state = 'turning'

    def move(self, direction, speed=3):
        """
            Ask movement in the direction of <angle>, <speed>
        """
        if speed > tank_speed:
            speed = tank_speed
        self.vector = Vector(direction, speed)
        self.target_coord = self.coord + self.vector * 100  # далеко-далеко...
        self._need_moving = True
        if self._need_turning():
            self._state = 'turning'
        else:
            self._state = 'moving'

    def move_at(self, target, speed=3):
        """
            Ask movement to the specified point
            <object/point/coordinats>, <speed>
        """
        if type(target) in (type(()), type([])):
            target = Point(target)
        elif target.__class__ == Point:
            pass
        elif isinstance(target, GameObject):
            target = target.coord
        else:
            raise Exception("move_at: target %s must be coord "
                            "or point or GameObject!" % target)
        if speed > tank_speed:
            speed = tank_speed
        self.target_coord = target
        self.vector = Vector(self.coord, self.target_coord, speed)
        self._need_moving = True
        if self._need_turning():
            self._state = 'turning'
        else:
            self._state = 'moving'

    def stop(self):
        """
            Unconditional stop
        """
        self._state = 'stopped'
        self._need_moving = False
        self._events.put(EventStopped())

    def _game_step(self):
        """
            Proceed one game step - do turns, movements and boundary check
        """
        self.debug('obj step %s', self)
        if self._revolvable and self._state == 'turning':
            delta = self.vector.angle - self.course
            if abs(delta) < tank_turn_speed:
                self.course = self.vector.angle
                if self._need_moving:
                    self._state = 'moving'
                else:
                    self._state = 'stopped'
                    self._events.put(EventStopped())
            else:
                if -180 < delta < 0 or delta > 180:
                    self.course -= tank_turn_speed
                else:
                    self.course += tank_turn_speed
                self.course = normalise_angle(self.course)

        if self._state == 'moving':
            self.coord.add(self.vector)
            if self.coord.near(self.target_coord):
                self.stop()
                self._events.put(EventStoppedAtTargetPoint(
                    self.target_coord))
        # boundary_check
        left_ro = self._runout(self.coord.x)
        if left_ro:
            self.coord.x += left_ro + 1
            self.stop()
        botm_ro = self._runout(self.coord.y)
        if botm_ro:
            self.coord.y += botm_ro + 1
            self.stop()
        righ_ro = self._runout(self.coord.x, field_width)
        if righ_ro:
            self.coord.x -= righ_ro + 1
            self.stop()
        top_ro = self._runout(self.coord.y, field_height)
        if top_ro:
            self.coord.y -= top_ro + 1
            self.stop()

        self._heartbeat_tics -= 1
        if not self._heartbeat_tics:
            event = EventHearbeat()
            self._events.put(event)
            self.hearbeat()
            self._heartbeat_tics = 5

    def _runout(self, coordinate, hight_bound=None):
        """
            proverka vyhoda za granicy igrovogo polja
        """
        if hight_bound:
            out = coordinate - (hight_bound - self.radius)
        else:
            out = self.radius - coordinate
        if out < 0:
            out = 0
        return out

    def distance_to(self, obj):
        """
            Calculate distance to <object/point>
        """
        if isinstance(obj, GameObject):  # и для порожденных классов
            return self.coord.distance_to(obj.coord)
        if obj.__class__ == Point:
            return self.coord.distance_to(obj)
        raise Exception("GameObject.distance_to: obj %s "
                        "must be GameObject or Point!" % (obj,))

    def near(self, obj, radius=20):
        """
            Is it near to the <object/point>?
        """
        return self.distance_to(obj) <= radius

    def _proceed_events(self):
        while not self._events.empty():
            event = self._events.get()
            event.handle(self)

    def stopped(self):
        """
            Event: stopped
        """
        pass

    def stopped_at_target(self):
        """
            Event: stopped at target
        """
        pass

    def hearbeat(self):
        """
            Event: Heartbeat
        """
        pass


class Gun:
    states = ['reloading', 'loaded']

    def __init__(self, owner):
        self.owner = owner
        self.heat = 8
        self._state = 'reloading'

    def _game_step(self):
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
            start_point = Point(self.owner.coord) + \
                          Vector(self.owner.course,
                                          self.owner.radius // 2 + 12)
            shot = Shot(pos=start_point, direction=self.owner.course)
            self.heat = tank_gun_heat_after_fire
            self._state = 'reloading'
            return shot


class Tank(GameObject):
    """
        Tank. May ride on the screen.
    """
    _selectable = True  # обьект можно выделить мышкой

    _img_file_name = 'tank_blue.png'
    _layer = 2
    radius = 32  # collision detect

    def __init__(self, pos=None, angle=None):
        """
            create a tank in a specified point on the screen
        """
        if not pos:
            pos = random_point(self.radius)
        GameObject.__init__(self, pos, angle=angle)
        self.gun = Gun(self)
        self._armor = float(tank_max_armor)
        self.explosion = None
        self._events.put(EventBorn())

    @property
    def armor(self):
        return int(self._armor)

    @property
    def gun_heat(self):
        return self.gun.heat

    def _game_step(self):
        """
            Internal function to update the state variables
        """
        if self._armor < tank_max_armor:
            self._armor += tank_armor_renewal_rate
        self.gun._game_step()
        self._update_explosion()
        GameObject._game_step(self)

    def _update_explosion(self):
        """
            Renew exploison at the armor - it must moving with as
        """
        if self.explosion:
            self.explosion.coord = Point(self.coord)
            self.debug("tank course %s explosion.vector.angle %s "
                       "explosion.coord %s", self.course,
                       self.explosion.vector.angle, self.explosion.coord)
            expl_shift = Vector(self.course
                                         + self.explosion.vector.angle,
                                         self.explosion.vector.module)
            self.explosion.coord.add(expl_shift)
            self.debug("after add explosion is %s", self.explosion)

    def fire(self):
        """
            Make shot.
        """
        self.shot = self.gun.fire()
        if self.shot:
            self.shot.owner = self

    def detonate(self):
        """
            Suicide
        """
        self.stop()
        Explosion(self.coord, self)  # взрыв на нашем месте
        if self in self.container:
            self.container.remove(self)

    def hit(self, shot):
        """
            Contact with our tank shell
        """
        self._armor -= shot.power
        self._events.put(EventHit())
        if self._armor <= 0:
            if shot.owner:  # еще не был убит
                shot.owner._events.put(EventTargetDestroyed())
            self.detonate()

    def born(self):
        """
            Event: born
        """
        pass

    def stopped(self):
        """
            Event: stopped
        """
        pass

    def stopped_at_target_point(self, point):
        """
            Event: stopped near the target
        """
        pass

    def gun_reloaded(self):
        """
            Event: the gun is ready to fire
        """
        pass

    def hitted(self):
        """
            Event: contact with our tank shell
        """
        pass

    def collided_with(self, obj):
        """
            Event: contact with our tank shell
        """
        pass

    def target_destroyed(self):
        """
            Event: contact with our tank shell
        """
        pass

    def in_tank_radar_range(self, objects):
        """
            Event: contact with our tank shell
        """
        pass


class StaticTarget(Tank):
    """
        A static target
    """
    _img_file_name = 'tank_red.png'
    _selectable = False  # обьект нельзя выделить мышкой

    def __init__(self, pos=None, angle=None, auto_fire=False):
        Tank.__init__(self, pos=pos, angle=angle)
        self.auto_fire = auto_fire

    def gun_reloaded(self):
        if self.auto_fire:
            self.fire()


class Target(Tank):
    """
        A target
    """
    _img_file_name = 'tank_red.png'
    _selectable = False  # обьект нельзя выделить мышкой

    def __init__(self, pos=None, angle=None, auto_fire=False):
        Tank.__init__(self, pos=pos, angle=angle)
        self.auto_fire = auto_fire

    def born(self):
        self.move_at(random_point())

    def stopped(self):
        self.debug("stopped")
        self.move_at(random_point())

    def gun_reloaded(self):
        self.debug("gun_reloaded")
        if self.auto_fire:
            self.fire()

    def collided_with(self, obj):
        self.debug("collided_with %s", obj.id)
        self.move_at(random_point())


class Shot(GameObject):
    """
        The shell. Flies in a straight until it hits the target.
    """
    _img_file_name = 'shot.png'
    _layer = 3
    radius = 4  # collision detect
    _selectable = False  # обьект нельзя выделить мышкой

    def __init__(self, pos, direction):
        """
            Start a shell from a specified point in the direction of the

            Zapustit' snarjad iz ukazannoj tochki v ukazannom napravlenii
        """
        GameObject.__init__(self, pos, revolvable=False)
        self.move(direction, shot_speed)
        self.life = shot_life
        self.power = shot_power

    def detonate_at(self, obj):
        """
            Explosion!
        """
        SmallExplosion(self.coord, obj)  # взрыв на месте снаряда
        self.container.remove(self)
        if self.owner:
            self.owner.shot = None
            self.owner = None

    def _game_step(self):
        self.debug('%s', self)
        self.life -= 1
        if not self.life or not self._state == 'moving':
            self.owner.shot = None
            self.container.remove(self)
        GameObject._game_step(self)


class Explosion(GameObject):
    """
        The explosion of the tank.
    """
    # TODO подумать куда отнести взрывы,
    # TODO ведь в игоровой механике они не участвуют
    _img_file_name = 'explosion.png'
    _layer = user_interface._max_layers
    radius = 0  # collision detect
    defaultlife = 12
    animcycle = 3
    _selectable = False  # обьект нельзя выделить мышкой
    _animated = True  # надо анимировать обьект TODO сделать анимацию в гифке

    def __init__(self, explosion_coord, hitted_obj):
        GameObject.__init__(self, explosion_coord, revolvable=False)
        self.vector = Vector(hitted_obj.coord, explosion_coord)
        self.vector.angle -= hitted_obj.course  # смещение при отображении
        self.owner = hitted_obj
        self.owner.explosion = self
        self.owner._update_explosion()
        self.life = self.defaultlife

    def _game_step(self):
        self.life -= 1
#        self.image = self.images[self.life // self.animcycle % 2]
        if self.life <= 0:
            self.container.remove(self)
            self.owner.explosion = None
            self.owner = None
        GameObject._game_step(self)


class SmallExplosion(Explosion):
    """
        The explosion of the shell.
    """
    _img_file_name = 'small_explosion.png'
