#!/usr/bin/env python
# -*- coding: utf-8 -*-

import constants
from math import *


def from_screen(coord):
    """Преобразовать координаты из экранных"""
    return coord[0], constants.field_height - coord[1]


def normalise_angle(a):
    #~ if a >= 360:
        #~ return a%360
    #~ if a < 0:
        #~ return abs(a)%360 + 360
    return a % 360


def get_arctan(dy, dx):
    out = atan2(dy, dx) / pi * 180
    # Unlike atan(y/x), the signs of both x and y are considered.
    return normalise_angle(out)


#~ _tangens_cache = {}
def get_tangens(angle):
    return tan(angle / 180.0 * pi)
    #~ angle = int(angle)
    #~ if angle in _tangens_cache:
        #~ return _tangens_cache[angle]
    #~ val = tan(angle / 180.0 * pi)
    #~ _tangens_cache[angle] = val
    #~ return val


class Point():
    """Класс точки на экране"""

    #~ int_x = property(lambda self: round(self.x),
    # doc="Округленная до пиксела координата X")
    #~ int_y = property(lambda self: round(self.y),
    # doc="Округленная до пиксела координата Y")

    def __init__(self, arg1, arg2=None):
        """Создать точку. Можно создать из другой точки, из списка/тьюпла
        или из конкретных координат"""
        if hasattr(arg1, 'coord'):
            self.x = arg1.coord.x
            self.y = arg1.coord.y
        elif hasattr(arg1, 'x'):
            self.x = arg1.x
            self.y = arg1.y
        elif type(arg1) == type([]) or type(arg1) == type(()):
            self.x, self.y = arg1
        elif type(arg1) == type(42) or type(arg1) == type(27.0):
            self.x, self.y = arg1, arg2
        else:
            raise Exception(self.__init__.__doc__)
        #~ log.debug(str(self))

    def to_screen(self):
        """Преобразовать координаты к экранным"""
        return int(self.x), constants.field_height - int(self.y)

    def add(self, vector):
        """Прибавить вектор - точка смещается на вектор"""
        self.x += vector.dx
        self.y += vector.dy

    def __add__(self, vector):
        if vector.__class__ != Vector:
            raise Exception('point will add only vector')
        return Point(self.x + vector.dx,
                       self.y + vector.dy)

    def sub(self, vector):
        """Вычесть вектор - точка смещается на "минус" вектор"""
        self.x -= vector.dx
        self.y -= vector.dy

    def __sub__(self, vector):
        if vector.__class__ != Vector:
            raise Exception('point will sub only vector')
        return Point(self.x - vector.dx,
                       self.y - vector.dy)

    def distance_to(self, point2):
        """Расстояние до другой точки"""
        return sqrt((self.x - point2.x) ** 2 + (self.y - point2.y) ** 2)

    def near(self, point2, radius=5):
        """Признак расположения рядом с другой точкой,
        рядом - это значит ближе, чем радиус"""
        return self.distance_to(point2) < radius

    def __eq__(self, point2):
        """Сравнение двух точек на равенство целочисленных координат"""
        #~ if point2:
            #~ print self, point2
        if  int(self.x) == int(point2.x) and int(self.y) == int(point2.y):
            return True
        return False

    def __str__(self):
        """Преобразование к строке"""
        return 'p(%.1f,%.1f)' % (self.x, self.y)

    def __repr__(self):
        """Представление """
        return str(self)

    def __iter__(self):
        yield self.x
        yield self.y

    def __getitem__(self, ind):
        if ind:
            return self.y
        return self.x

    def __nonzero__(self):
        if self.x and self.y:
            return 1
        return 0


class Vector():
    """Класс математического вектора"""

    def __init__(self, arg1, arg2, arg3=None):
        """Создать вектор. Можно создать:
            двух точек arg1, arg2 (длинной в модуль arg3, если указан)
            направление arg1 и модуль вектора arg2
        """
        #~ log.debug("vector init (%s, %s, %s)", arg1, arg2, arg3)
        self.dx, self.dy, self.angle = 0, 0, None

        if hasattr(arg1, 'x') or hasattr(arg1, 'coord'):  # Point or GameObject
            if hasattr(arg1, 'x'):
                point1, point2 = arg1, arg2
            else:
                point1, point2 = arg1.coord, arg2.coord
            self.dx = float(point2.x - point1.x)
            self.dy = float(point2.y - point1.y)
            self._determine_module()
            self._determine_angle()
            if arg3 != None:  # указан модуль - ограничиваем (None не убирать!)
                module = arg3
                if self.module:
                    self.dx *= module / self.module
                    self.dy *= module / self.module
                self.module = module
        elif arg1.__class__ == int or arg1.__class__ == float or \
             arg2.__class__ == int or arg2.__class__ == float:
            direction, module = arg1, arg2
            direction_rad = (direction * pi) / 180
            self.dx = cos(direction_rad) * module
            self.dy = sin(direction_rad) * module
            self.angle = normalise_angle(direction)
            self.module = module
        else:
            raise Exception(Vector.__init__.__doc__)

    def add(self, vector2):
        """Сложение векторов"""
        self.dx += vector2.dx
        self.dy += vector2.dy
        self._determine_module()
        self._determine_angle()

    def mul(self, raz):
        """умножение вектора на число"""
        self.dx *= raz
        self.dy *= raz
        self._determine_module()
        self._determine_angle()

    def _determine_module(self):
        self.module = sqrt(self.dx ** 2 + self.dy ** 2)

    def _determine_angle(self):
        self.angle = 0
        if self.dx == 0:
            if self.dy >= 0:
                a = 90
            else:
                a = 270
        else:
            a = atan(self.dy / self.dx) * (180 / pi)
            if self.dx < 0:
                a += 180
        self.angle = normalise_angle(a)

    def __str__(self):
        return 'v(dx=%.2f dy=%.2f a=%.2f m=%.2f)' \
                % (self.dx, self.dy, self.angle, self.module)

    def __repr__(self):
        return str(self)

    def __nonzero__(self):
        """Проверка на пустоту"""
        return int(self.module)

    def __neg__(self):
        ret = Vector(0, 0)
        ret.dx = -self.dx
        ret.dy = -self.dy
        return ret

    def __add__(self, other):
        return Vector(self.dx + other.dx,
                       self.dy + other.dy)

    def __mul__(self, int_arg):
        return Vector(self.dx * int_arg,
                       self.dy * int_arg)
