#!/usr/bin/env python
# -*- coding: utf-8 -*-

import events
import common
import geometry
import user_interface
import constants
import Queue
from random import randint


class GameObject():
    """
        Main game object

        Glavnyj igrovoj ob'ekt
    """
    radius = 1
    __name__ = 'GameObject'
    _objects_count = 0
    states = ['stopped', 'turning', 'moving']
    container = None

    def __init__(self, pos, revolvable=True, angle=None):
        self.coord = geometry.Point(pos)
        self.target_coord = geometry.Point(0, 0)

        if angle is None:
            angle = randint(0, 360)
        self.vector = geometry.Vector(angle, 0)
        self.course = self.vector.angle
        self.shot = False
        self.revolvable = revolvable
        self.load_value = 0
        self._distance_cache = {}
        self._events = Queue.Queue()
        self._selected = False
        self._state = 'stopped'
        self._need_moving = False

        # container - это список, обьявлен на уровне порожденного класса,
        # инициализируется в Scene
        self.container.append(self)

        GameObject._objects_count += 1
        self._id = GameObject._objects_count
        self.debug('born %s', self)

        self._heartbeat_tics = 5

    def __str__(self):
        return 'obj(%s, %s %s cour=%.1f %s)' \
                % (self._id, self.coord, self.vector,
                   self.course, self._state)

    def __repr__(self):
        return str(self)

    def debug(self, pattern, *args):
        """
            Show debug information if DEBUG mode

            Pokazyvat' otladochnuyu informatsiyu esli vklyuchen rezhim otladki
        """
        if isinstance(self, Tank):
            if self._selected:
                common.log.debug('%s:%s' % (self._id, pattern), *args)
        else:
            common.log.debug('%s:%s:%s' % (self.__class__.__name__,
                                           self._id, pattern), *args)

    def type(self):
        return self.__name__

    def _need_turning(self):
        return self.revolvable and int(self.course) != int(self.vector.angle)

    def turn_to(self, arg1):
        """
            Turn to the subject / in that direction

            Povernut'sja k ob'ektu / v ukazanom napravlenii
        """
        if isinstance(arg1, GameObject) or arg1.__class__ == geometry.Point:
            self.vector = geometry.Vector(self, arg1, 0)
        elif arg1.__class__ == int or arg1.__class__ == float:
            direction = arg1
            self.vector = geometry.Vector(direction, 0)
        else:
            raise Exception("use GameObject.turn_to(GameObject/Point "
                            "or Angle). Your pass %s" % arg1)
        self._state = 'turning'

    def move(self, direction, speed=3):
        """
            Ask movement in the direction of <angle>, <speed>

            Zadat' dvizhenie v napravlenii <ugol v gradusah>, <skorost'>
        """
        if speed > constants.tank_speed:
            speed = constants.tank_speed
        self.vector = geometry.Vector(direction, speed)
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

            Zadat' dvizhenie k ukazannoj tochke
            <ob'ekt/tochka/koordinaty>, <skorost'>
        """
        if type(target) in (type(()), type([])):
            target = geometry.Point(target)
        elif target.__class__ == geometry.Point:
            pass
        elif isinstance(target, GameObject):
            target = target.coord
        else:
            raise Exception("move_at: target %s must be coord "
                            "or point or GameObject!" % target)
        if speed > constants.tank_speed:
            speed = constants.tank_speed
        self.target_coord = target
#        self.debug('before vector %s %s %s',
#        self.coord, self.target_coord, speed)
        self.vector = geometry.Vector(self.coord, self.target_coord, speed)
#        self.debug('after vector %s', self)
        self._need_moving = True
        if self._need_turning():
            self._state = 'turning'
        else:
            self._state = 'moving'

    def stop(self):
        """
            Unconditional stop

            Ostanovit' ob'ekt
        """
        self._state = 'stopped'
        self._need_moving = False
        self._events.put(events.EventStopped())

    def _game_step(self):
        """
            Internal function

            Vnutrennjaja funkcija dlja dvizhenija/povorota
            i proverki vyhoda za granicy jekrana
        """
        self.debug('obj step %s', self)
        if self.revolvable and self._state == 'turning':
            delta = self.vector.angle - self.course
            if abs(delta) < constants.tank_turn_speed:
                self.course = self.vector.angle
                if self._need_moving:
                    self._state = 'moving'
                else:
                    self._state = 'stopped'
                    self._events.put(events.EventStopped())
            else:
                if -180 < delta < 0 or delta > 180:
                    self.course -= constants.tank_turn_speed
                else:
                    self.course += constants.tank_turn_speed
                self.course = geometry.normalise_angle(self.course)

        if self._state == 'moving':
#            self.debug('%s adding %s ', self.coord, self.vector)
            self.coord.add(self.vector)
            if self.coord.near(self.target_coord):
                self.stop()
                self._events.put(events.EventStoppedAtTargetPoint(
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
        righ_ro = self._runout(self.coord.x, constants.field_width)
        if righ_ro:
            self.coord.x -= righ_ro + 1
            self.stop()
        top_ro = self._runout(self.coord.y, constants.field_height)
        if top_ro:
            self.coord.y -= top_ro + 1
            self.stop()

        self._heartbeat_tics -= 1
        if not self._heartbeat_tics:
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

            Rasstojanie do ob'ekta <ob#ekt/tochka>
        """
        if isinstance(obj, GameObject):  # и для порожденных классов
            return self.coord.distance_to(obj.coord)
            #~ if obj._id in self._distance_cache:
                #~ return self._distance_cache[obj._id]
            #~ dist = self.coord.distance_to(obj.coord)
            #~ self._distance_cache[obj._id] = dist
            #~ obj._distance_cache[self._id] = dist
            #~ return dist
        if obj.__class__ == geometry.Point:
            #~ print 'distance_to Point'
            return self.coord.distance_to(obj)
        raise Exception("GameObject.distance_to: obj %s "
                        "must be GameObject or Point!" % (obj,))

    def near(self, obj, radius=20):
        """
            Is we near to the <object/point>?

            Proverka blizosti k ob'ektu <ob'ekt/tochka>
        """
        return self.distance_to(obj) <= radius

#    def step_back(self):
#        self.coord.add(-self.vector)

    def _proceed_events(self):
        while not self._events.empty():
            event = self._events.get()
            event.handle(self)

    def stopped(self):
        """
            Event: stopped

            Sobytie: ostanovka
        """
        pass

    def stopped_at_target(self):
        """
            Event: stopped at target

            Sobytie: ostanovka u celi
        """
        pass

    def hearbeat(self):
        """
            Event: Heartbeat

            sobytie: pul'sacija zhizni
        """
        pass


class Gun:
    __name__ = 'Gun'
    states = ['reloading', 'loaded']

    def __init__(self, owner):
        self.owner = owner
        self.heat = 8
        self._state = 'reloading'

    def _game_step(self):
        """
            Internal function

            Vnutrennjaja funkcija dlja obnovlenija peremennyh sostojanija
        """
        if self._state == 'reloading':
            self.heat -= 1
            if not self.heat:
                # перезарядка только что кончилась
                self.owner._events.put(events.EventGunReloaded())
                self._state = 'loaded'

    def fire(self):
        """
            Fire from gun

            vystrelit' iz pushki
        """
        if self._state == 'loaded':
            start_point = geometry.Point(self.owner.coord) + \
                          geometry.Vector(self.owner.course,
                                          self.owner.radius // 2 + 12)
            shot = Shot(pos=start_point, direction=self.owner.course)
            self.heat = constants.tank_gun_heat_after_fire
            self._state = 'reloading'
            return shot


class Tank(GameObject, user_interface.MshpSprite):
    """
        Tank. May ride on the screen.

        Tank. Mozhet ezdit' po jekranu.
    """
    __name__ = 'Tank'
    _img_file_name = 'tank_blue.png'
    _layer = 2
    radius = 32  # collision detect

    def __init__(self, pos=None, angle=None):
        """
            create a tank in a specified point on the screen

            sozdat' tank v ukazannoj tochke jekrana
        """
        if not pos:
            pos = common.random_point(self.radius)
        GameObject.__init__(self, pos, angle=angle)
        user_interface.MshpSprite.__init__(self)
        self.gun = Gun(self)
        self._armor = float(constants.tank_max_armor)
        self.explosion = None
        self._events.put(events.EventBorn())

    @property
    def armor(self):
        return int(self._armor)

    def _game_step(self):
        """
            Internal function to update the state variables

            Vnutrennjaja funkcija dlja obnovlenija peremennyh sostojanija
        """
        if self._armor < constants.tank_max_armor:
            self._armor += constants.tank_armor_renewal_rate
        self.gun._game_step()
        self._update_explosion()
        GameObject._game_step(self)

    def _update_explosion(self):
        """
            Обновить взрыв на броне - должен двигаться с нами :)
        """
        if self.explosion:
            #~ print '+'*20
            #~ print self
            #~ print self.explosion
            self.explosion.coord = geometry.Point(self.coord)
            #~ print self.course, self.explosion.vector.angle
            self.debug("tank course %s explosion.vector.angle %s "
                       "explosion.coord %s", self.course,
                       self.explosion.vector.angle, self.explosion.coord)
            expl_shift = geometry.Vector(self.course
                                         + self.explosion.vector.angle,
                                         self.explosion.vector.module)
            self.explosion.coord.add(expl_shift)
            self.debug("after add explosion is %s", self.explosion)
            #~ print self.explosion

    def fire(self):
        """
            Make shot.

            vystrelit' iz pushki
        """
        self.shot = self.gun.fire()
        if self.shot:
            self.shot.owner = self

    def detonate(self):
        """
            Suicide

            Samopodryv...
        """
        self.stop()
        Explosion(self.coord, self)  # взрыв на нашем месте
        self.kill()
        if self in self.container:
            self.container.remove(self)

    def hit(self, shot):
        """
            Contact with our tank shell

            Popadanie v nash tank snarjada
        """
        self._armor -= shot.power
        self._events.put(events.EventHit())
        #~ print self._id, 'hited! armor now ', self.armor
        if self._armor <= 0:
            if shot.owner:  # еще не был убит
                shot.owner._events.put(events.EventTargetDestroyed())
            self.detonate()

    def born(self):
        """
            Event: born

            Sobytie: rozhdenie
        """
        pass

    def stopped(self):
        """
            Event: stopped

            Sobytie: ostanovka
        """
        pass

    def stopped_at_target_point(self, point):
        """
            Event: stopped near the target

            Sobytie: ostanovka u celi
        """
        pass

    def gun_reloaded(self):
        """
            Event: the gun is ready to fire

            Sobytie: pushka gotova k vystrelu
        """
        pass

    def hitted(self):
        """
            Event: contact with our tank shell

            Sobytie: chuzhoj snarjad popal v bronju
        """
        pass

    def collided_with(self, obj):
        """
            Event: contact with our tank shell

            Sobytie: stolknovenie s ob'ektom
        """
        pass

    def target_destroyed(self):
        """
            Event: contact with our tank shell

            Sobytie: nash snarjad popal v ob'ekt i ob'ekt unichtozhen
        """
        pass

    def in_tank_radar_range(self, objects):
        """
            Event: contact with our tank shell

            Sobytie: radar obnaruzhil ob'ekty
        """
        pass


class StaticTarget(Tank):
    """
        A static target

        Statichnaja mishen'
    """
    __name__ = 'StaticTarget'
    _img_file_name = 'tank_red.png'

    def __init__(self, pos=None, angle=None, auto_fire=False):
        Tank.__init__(self, pos=pos, angle=angle)
        self.auto_fire = auto_fire

    def gun_reloaded(self):
        if self.auto_fire:
            self.fire()


class Target(Tank):
    """
        A target

        Mishen'
    """
    __name__ = 'Target'
    _img_file_name = 'tank_red.png'

    def __init__(self, pos=None, angle=None, auto_fire=False):
        Tank.__init__(self, pos=pos, angle=angle)
        self.auto_fire = auto_fire

    def born(self):
        self.move_at(common.random_point())

    def stopped(self):
        self.debug("stopped")
        self.move_at(common.random_point())

    def gun_reloaded(self):
        self.debug("gun_reloaded")
        if self.auto_fire:
            self.fire()

    def collided_with(self, obj):
        self.debug("collided_with %s", obj._id)
        self.move_at(common.random_point())


class Shot(GameObject, user_interface.MshpSprite):
    """
        The shell. Flies in a straight until it hits the target.

        Snarjad. Letit po prjamoj poka ne vstretit cel'.
    """
    __name__ = 'Shot'
    _img_file_name = 'shot.png'
    _layer = 3
    radius = 4  # collision detect

    def __init__(self, pos, direction):
        """
            Start a shell from a specified point in the direction of the

            Zapustit' snarjad iz ukazannoj tochki v ukazannom napravlenii
        """
        GameObject.__init__(self, pos, revolvable=False)
        user_interface.MshpSprite.__init__(self)
        self.move(direction, constants.shot_speed)
        self.life = constants.shot_life
        self.power = constants.shot_power

    def detonate_at(self, obj):
        """
            Explosion!

            vzryv!
        """
        SmallExplosion(self.coord, obj)  # взрыв на месте снаряда
        self.kill()  # as MshpSprite instance
        if self.owner:
            self.owner.shot = None
            self.owner = None

    def _game_step(self):
        self.debug('%s', self)
        self.life -= 1
        if not self.life or not self._state == 'moving':
            self.kill()
            self.owner.shot = None
            self.container.remove(self)
        GameObject._game_step(self)


class Explosion(GameObject, user_interface.MshpSprite):
    """
        The explosion of the tank.

        Vzryv tanka.
    """
    __name__ = 'Explosion'
    _img_file_name = 'explosion.png'
    _layer = user_interface._max_layers
    radius = 0  # collision detect
    defaultlife = 12
    animcycle = 3

    def __init__(self, explosion_coord, hitted_obj):
        GameObject.__init__(self, explosion_coord, revolvable=False)
        user_interface.MshpSprite.__init__(self)
        self.vector = geometry.Vector(hitted_obj.coord, explosion_coord)
        self.vector.angle -= hitted_obj.course  # смещение при отображении
        self.owner = hitted_obj
        self.owner.explosion = self
        self.owner._update_explosion()
        self.life = self.defaultlife

    def _game_step(self):
        self.life -= 1
        self.image = self.images[self.life // self.animcycle % 2]
        if self.life <= 0:
            self.kill()
            self.container.remove(self)
            self.owner.explosion = None
            self.owner = None
        GameObject._game_step(self)


class SmallExplosion(Explosion):
    """
        The explosion of the shell.

        Vzryv snarjada.
    """
    __name__ = 'SmallExplosion'
    _img_file_name = 'small_explosion.png'
