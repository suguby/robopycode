#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
from pygame.locals import *
from pygame.sprite import Sprite, DirtySprite, Group
from pygame.font import Font
from pygame.transform import flip
from pygame.draw import line, circle, rect, aalines
from pygame.display import set_caption, set_mode
from pygame.time import Clock
import time
import common
import constants
import os
import random
from geometry import Point

_debug = common._debug
log = common.log
_max_layers = 5
_sprites_by_layer = [Group() for i in range(_max_layers + 1)]
_images_cash = {}

class RoboSprite(DirtySprite):
    """
        Show sprites on screen
    """
    _img_file_name = 'empty.png'
    _layer = 0

    def __init__(self, id, state):
        """
            Link object with its sprite
        """
        self.id = id
        self.state = state

        if self._layer > _max_layers:
            self._layer = _max_layers
        if self._layer < 0:
            self._layer = 0
        self.sprite_containers = (self.sprite_containers,
                                  _sprites_by_layer[self._layer])
        Sprite.__init__(self, self.sprite_containers)

        image = load_image(self.state._img_file_name, -1)
        self.images = [image, flip(image, 1, 0), flip(image, 0, 1), flip(image, 1, 1)]
        self.image = self.images[0].copy()
        self.rect = self.image.get_rect()
        self._debug_color = (
            random.randint(200, 255),
            random.randint(50, 255),
            0
           )
        self._id_font = Font(None, 27)
#        self._armor_pixels = 0
        self._selected = False
        # для отрисовки взрывов
        self._animcycle = 3
        self._drawed_count = 0

    def update_state(self, state):
        self.state = state

    def __str__(self):
        return 'sprite(%s: rect=%s layer=%s)' \
                % (self.id, self.rect, self._layer)

    def __repr__(self):
        return str(self)

    def _show_armor(self):
        if hasattr(self.state, 'armor') and self.state.armor > 0:
            bar_px = int((self.state.armor / 100.0) * self.rect.width)
            line(self.image, (0, 255, 70), (0, 3), (bar_px, 3), 3)

    def _show_gun_heat(self):
        if hasattr(self.state, 'gun_heat') and self.state.gun_heat > 0:
            max_heat = float(constants.tank_gun_heat_after_fire)
            bar_px = int(((max_heat - self.state.gun_heat)
                          / max_heat) * self.rect.width)
            line(self.image, (232, 129, 31), (0, 5),
                (bar_px, 5), 2)

    def _show_selected(self):
        if self._selected:
            outline_rect = pygame.Rect(0, 0,
                self.rect.width, self.rect.height)
            rect(self.image,
                self._debug_color, outline_rect, 1)

    def _show_tank_id(self):
        if hasattr(self, 'state') and hasattr(self.state, 'gun_heat'):
            id_image = self._id_font.render(str(self.id),
                0,
                self._debug_color)
            self.image.blit(id_image, (5, 5))

    def _show_detection(self):
        if hasattr(self.state, '_detected_by'):
            radius = 0
            for obj in self.state._detected_by:
                if obj._selected:
                    radius += 6
                    circle(self.image,
                        obj._debug_color,
                        (self.rect.width // 2,
                         self.rect.height // 2),
                        radius,
                        3)

    def update(self):
        """
            Internal function for refreshing internal variables.
            Do not call in your code!
        """
        self.rect.center = self.state.coord.to_screen()
        if self.state.revolvable:
            self.image = _rotate_about_center(self.images[0],
                                              self.state._img_file_name,
                                              self.state.course)
        elif self.state._animated:
            self._drawed_count += 1
            self.image = self.images[self._drawed_count // self._animcycle % 4]
        else:
            self.image = self.images[0].copy()

        self._show_armor()
        self._show_gun_heat()
        self._show_selected()
        if common._debug:
            self._show_tank_id()
            self._show_detection()

class UserInterfaceState:
    """
        Класс для передачи состояния клавиатуры и мыши
    """
    def __init__(self):
        self.one_step = False
        self.switch_debug = False
        self.the_end = False
        self.mouse_pos = None
        self.mouse_buttons = None
        self.selected_ids = []

class UserInterface:
    """
        Show sprites and get feedback from user
    """
    def __init__(self, name):
        """
            Make game window
        """
        global SCREENRECT

        pygame.init()
        SCREENRECT = Rect((0, 0),
                          (constants.field_width, constants.field_height))
        self.screen = set_mode(SCREENRECT.size)
        set_caption(name)

        self.background = pygame.Surface(self.screen.get_size())  # и ее размер
        self.background = self.background.convert()
        self.background.fill(constants.background_color)  # заполняем цветом
        self.clear_screen()

        self.all = pygame.sprite.LayeredUpdates()
        RoboSprite.sprite_containers = self.all
        Fps.sprite_containers = self.all

        global clock
        clock = Clock()

        self.fps_meter = Fps(color=(255, 255, 0))
        self.max_fps = constants.max_fps

        self._step = 0
        self.debug = False

        self.game_objects = {}

    def run(self, child_conn):
        self.child_conn = child_conn
        while True:
            try:
                if self.child_conn.poll(0.01):
                    objects_state = self.child_conn.recv()
                    ui_state = self.communicate(objects_state)
                    self.child_conn.send(ui_state)
                self.draw()
            except Exception, exc:
                print exc

    def communicate(self, objects_state):
        """
            зарегестрировать состояния обьектов игры, создать/удалить спрайты если надо
            вернуть состояния клавиатуры и мыши
        """
        new_ids = set(objects_state)
        old_ids = set(self.game_objects)
        new_game_objects = {}

        for id in old_ids - new_ids:
            # старые объекты - убиваем спрайты
            sprite = self.game_objects[id]
            sprite.kill()

        for id in new_ids - old_ids:
            # новые объекты - создаем спрайты
            sprite = RoboSprite(id=id, state=objects_state[id])
            new_game_objects[id] = sprite

        for id in old_ids & new_ids:
            # существующие объекты - обновляем состояния
            sprite = self.game_objects[id]
            state = objects_state[id]
            sprite.update_state(state)
            new_game_objects[id] = sprite

        self.game_objects = new_game_objects

        # преобразуем список айдишников в список обьектов
        for obj_id, obj in self.game_objects.iteritems():
            obj.state._detected_by = [
                self.game_objects[detected_by_id]
                for detected_by_id in obj.state._detected_by
                if detected_by_id in self.game_objects
            ]

        self.ui_state = UserInterfaceState()

        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_f:
                self.fps_meter.show = not self.fps_meter.show

            if (event.type == QUIT)\
               or (event.type == KEYDOWN and event.key == K_ESCAPE)\
            or (event.type == KEYDOWN and event.key == K_q):
                self.ui_state.the_end = True
            if event.type == KEYDOWN and event.key == K_d:
                self.ui_state.switch_debug = True
            if event.type == KEYDOWN and event.key == K_s:
                self.ui_state.one_step = True
        key = pygame.key.get_pressed()
        if key[pygame.K_g]:  # если нажата и удерживается
            self.ui_state.one_step = True
        pygame.event.pump()

        self._select_objects()

        if self.ui_state.switch_debug and common._debug:
            # были в режиме отладки
            self.clear_screen()

        return self.ui_state

    def _select_objects(self):
        """
            выделение обьектов мышкой
        """
        self.ui_state.mouse_pos = pygame.mouse.get_pos()
        self.ui_state.mouse_buttons = pygame.mouse.get_pressed()

        if self.ui_state.mouse_buttons[0] and not self.mouse_buttons[0]:
            # mouse down
            for obj_id, obj in self.game_objects.iteritems():
                if obj.state._selectable and obj.rect.collidepoint(self.ui_state.mouse_pos):
                    # координаты экранные
                    obj._selected = not obj._selected
                elif not common._debug:
                    # возможно выделение множества танков
                    # только на режиме отладки
                    obj._selected = False
        self.mouse_buttons = self.ui_state.mouse_buttons
        self.ui_state.selected_ids = [
            _id for _id in self.game_objects
            if self.game_objects[_id]._selected
        ]

    def clear_screen(self):
        self.screen.blit(self.background, (0, 0))
        pygame.display.flip()

    def _draw_radar_outline(self, obj):
        from math import pi, cos, sin
        angle_r = (obj.state.course - constants.tank_radar_angle // 2) / 180.0 * pi
        angle_l = (obj.state.course + constants.tank_radar_angle // 2) / 180.0 * pi
        coord = obj.state.coord
        points = [
            Point(coord.x + cos(angle_r) * constants.tank_radar_range,
                  coord.y + sin(angle_r) * constants.tank_radar_range),
            Point(coord.x + cos(angle_l) * constants.tank_radar_range,
                  coord.y + sin(angle_l) * constants.tank_radar_range),
            Point(coord.x,
                  coord.y)
        ]
        points = [x.to_screen() for x in points]
        aalines(self.screen,
                            obj._debug_color,
                            True,
                            points)

    def draw(self):
        """
            Drawing sprites on screen
        """

        #update all the sprites
        self.all.update()

        #draw the scene
        if common._debug:
            self.screen.blit(self.background, (0, 0))
            dirty = self.all.draw(self.screen)
            for obj in self.all:
                if hasattr(obj, 'state') and \
                   hasattr(obj.state, 'gun_heat') and \
                   obj._selected:
                    self._draw_radar_outline(obj)
            pygame.display.flip()
        else:
            # clear/erase the last drawn sprites
            self.all.clear(self.screen, self.background)
            dirty = self.all.draw(self.screen)
            pygame.display.update(dirty)

        #cap the framerate
        clock.tick(self.max_fps)
        return True


class Fps(DirtySprite):
    """
        Show game FPS
    """
    _layer = 5

    def __init__(self, color=(255, 255, 255)):
        """
            Make indicator
        """
        pygame.sprite.Sprite.__init__(self, self.sprite_containers)
        self.show = False
        self.font = pygame.font.Font(None, 27)
        self.color = color
        self.image = self.font.render('-', 0, self.color)
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(constants.field_width - 100, 10)
        self.fps = []

    def update(self):
        """
            Refresh indicator
        """
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
    """
        Load image from file
    """
    fullname = os.path.join(constants.data_path, name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error, message:
        print "Cannot load image:", fullname
        raise SystemExit(message)
        #image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image


def _rotate_about_center(image, image_name, angle):
    """
        rotate an image while keeping its center and size
    """
    global _images_cash
    angle = int(angle)
    try:
        return _images_cash[image_name][angle].copy()
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
