#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
from pygame.locals import *
import pygame.gfxdraw
import common
import constants
import os
import random
from geometry import Point

_debug = common._debug
log = common.log
_max_layers = 5
_sprites_by_layer = [pygame.sprite.Group() for i in range(_max_layers + 1)]
_images_cash = {}

#_revolvable = 0
#_determine_collisions = 1


class MshpSprite(pygame.sprite.DirtySprite):
    """Класс отображения объектов на экране"""
    _img_file_name = 'empty.png'
    _layer = 0

    def __init__(self):
        """Привязать объект к его спрайту"""

        if self._layer > _max_layers:
            self._layer = _max_layers
        if self._layer < 0:
            self._layer = 0
        self.sprite_containers = self.sprite_containers, _sprites_by_layer[self._layer]
        # , self.sprite_container
        pygame.sprite.Sprite.__init__(self, self.sprite_containers)

        image = load_image(self._img_file_name, -1)
        self.images = [image, pygame.transform.flip(image, 1, 0)]
        self.image = self.images[0].copy()
        self.rect = self.image.get_rect()
        self._debug_color = (
            random.randint(200, 255),
            random.randint(50, 255),
            0
           )
        self._id_font = pygame.font.Font(None, 27)

        self.armor_value_px = 0
        self.debug('MshpSprite %s', self)

    def __str__(self):
        return 'sprite(%s: rect=%s layer=%s)' \
                % (self._id, self.rect, self._layer)

    def __repr__(self):
        return str(self)

    def update(self):
        """Внутренняя функция для обновления переменных отображения"""
        self.rect.center = self.coord.to_screen()
        if self.revolvable:
            self.image = _rotate_about_center(self.images[0],
                                              self._img_file_name,
                                              self.course)
        else:
            self.image = self.images[0].copy()

        if hasattr(self, 'armor') and self.armor > 0:
            bar_px = int((self.armor / 100.0) * self.rect.width)
            pygame.draw.line(self.image, (0, 255, 70), (0, 3), (bar_px, 3), 3)
            #~ pygame.draw.line(self.image, (0,0,0), (0,0),
            #   (self.rect.width,0), 1)
            #~ pygame.draw.line(self.image, (0,0,0), (0,0),
            #   (0,self.rect.height), 1)
        if hasattr(self, 'gun') and self.gun.heat > 0:
            max_heat = float(constants.tank_gun_heat_after_fire)
            bar_px = int(((max_heat - self.gun.heat)
                          / max_heat) * self.rect.width)
            pygame.draw.line(self.image, (232, 129, 31), (0, 5), (bar_px, 5), 2)
            #~ pygame.draw.line(self.image, (0,0,0), (0,0),
            #   (self.rect.width,0), 1)
            #~ pygame.draw.line(self.image, (0,0,0), (0,0),
            #   (0,self.rect.height), 1)
        if self._selected:
            outline_rect = pygame.Rect(0, 0,
                                       self.rect.width, self.rect.height)
            #~ print outline_rect
            pygame.draw.rect(self.image,
                             self._debug_color, outline_rect, 1)
        if common._debug:
            if self.type() == 'Tank':
                id_image = self._id_font.render(str(self._id),
                                                0,
                                                self._debug_color)
                self.image.blit(id_image, (5, 5))
            if hasattr(self, '_detected_by') and self._detected_by:
                radius = 0
                for obj in self._detected_by:
                    if obj._selected:
                        radius += 6
                        pygame.draw.circle(self.image,
                                           obj._debug_color,
                                           (self.rect.width // 2,
                                            self.rect.height // 2),
                                           radius,
                                           3)


class UserInterface:
    """Отображение игры: отображение спрайтов
    и взаимодействия с пользователем"""

    def __init__(self, name):
        """Создать окно игры. """
        global SCREENRECT

        pygame.init()
        SCREENRECT = Rect((0, 0),
                          (constants.field_width, constants.field_height))
        self.screen = pygame.display.set_mode(SCREENRECT.size)
        pygame.display.set_caption(name)

        self.background = pygame.Surface(self.screen.get_size())  # и ее размер
        self.background = self.background.convert()
        self.background.fill(constants.background_color)  # заполняем цветом
        self.clear_screen()

        self.all = pygame.sprite.LayeredUpdates()
        MshpSprite.sprite_containers = self.all
        Fps.sprite_containers = self.all

        global clock
        clock = pygame.time.Clock()
        self.fps_meter = Fps(color=(255, 255, 0))
        self.max_fps = constants.max_fps

        self._step = 0
        self.debug = False

    def get_keyboard_and_mouse_state(self):
        self.one_step = False
        self.switch_debug = False
        self.the_end = False

        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_f:
                self.fps_meter.show = not self.fps_meter.show

            if (event.type == QUIT) \
                or (event.type == KEYDOWN and event.key == K_ESCAPE) \
                or (event.type == KEYDOWN and event.key == K_q):
                self.the_end = True
            if event.type == KEYDOWN and event.key == K_d:
                self.switch_debug = True
            if event.type == KEYDOWN and event.key == K_s:
                self.one_step = True
        key = pygame.key.get_pressed()
        if key[pygame.K_g]:  # если нажата и удерживается
            self.one_step = True
        pygame.event.pump()

        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_buttons = pygame.mouse.get_pressed()

    def clear_screen(self):
        self.screen.blit(self.background, (0, 0))
        pygame.display.flip()

    def _draw_radar_outline(self, obj):
        from math import pi, cos, sin
        angle_r = (obj.course - constants.tank_radar_angle // 2) / 180.0 * pi
        angle_l = (obj.course + constants.tank_radar_angle // 2) / 180.0 * pi
        points = [
            Point(obj.coord.x + cos(angle_r) * constants.tank_radar_range,
                  obj.coord.y + sin(angle_r) * constants.tank_radar_range),
            Point(obj.coord.x + cos(angle_l) * constants.tank_radar_range,
                  obj.coord.y + sin(angle_l) * constants.tank_radar_range),
            Point(obj.coord.x,
                  obj.coord.y)
        ]
        points = [x.to_screen() for x in points]
        pygame.draw.aalines(self.screen,
                            obj._debug_color,
                            True,
                            points)

    def draw(self):
        """Отрисовка спрайтов на экране"""

        #update all the sprites
#        for sprites in _sprites_by_layer:
#            sprites.update()
        self.all.update()

        #draw the scene
        if self.debug:
            self.screen.blit(self.background, (0, 0))
            dirty = self.all.draw(self.screen)
            for obj in self.all:
                if obj.type() == 'Tank' and obj._selected:
                    self._draw_radar_outline(obj)
#            [self._draw_radar_outline(obj) for obj in self.all \
#                        if obj.type() == 'Tank' and obj._selected]
            pygame.display.flip()
        else:
            # clear/erase the last drawn sprites
            self.all.clear(self.screen, self.background)
            dirty = self.all.draw(self.screen)
            pygame.display.update(dirty)

        #cap the framerate
        clock.tick(self.max_fps)
        return True


class Fps(pygame.sprite.DirtySprite):
    """Отображение FPS игры"""
    _layer = 5

    def __init__(self, color=(255, 255, 255)):
        """Создать индикатор FPS"""
        pygame.sprite.Sprite.__init__(self, self.sprite_containers)
        self.show = False
        self.font = pygame.font.Font(None, 27)
        self.color = color
        self.image = self.font.render('-', 0, self.color)
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(constants.field_width - 100, 10)
        self.fps = []

    def update(self):
        """Обновить значение FPS"""
        global clock
        current_fps = clock.get_fps()
        del self.fps[100:]
        self.fps.append(current_fps)
        if self.show:
            fps = sum(self.fps) / len(self.fps)
            msg = '%5.0f FPS' % fps
        else:
            msg = ''
        self.image = self.font.render(msg, 1, self.color)

    def type(self):
        return 'fps'


def load_image(name, colorkey=None):
    """Загрузить изображение из файла"""
    fullname = os.path.join(constants.__path__, 'data', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error, message:
        print "Cannot load image:", name
        raise SystemExit(message)
        #image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image


def _rotate_about_center(image, image_name, angle):
    """rotate an image while keeping its center and size"""
    global _images_cash
    angle = int(angle)
    try:
        return _images_cash[image_name][angle].copy()
        #~ log.debug("image [%s|%s] found in cashe", image_name, angle)
        #~ return ret
    except:
        orig_rect = image.get_rect()
        rot_image = pygame.transform.rotate(image, angle)
        rot_rect = orig_rect.copy()
        rot_rect.center = rot_image.get_rect().center
        rot_image = rot_image.subsurface(rot_rect).copy()
        try:
            _images_cash[image_name][angle] = rot_image
        except:
            _images_cash[image_name] = {angle: rot_image}
        return rot_image.copy()
