# -*- coding: utf-8 -*-


from multiprocessing import Process, Pipe
import pygame
from pygame.locals import *
from random import randint
from pygame.display import set_caption, set_mode
import time


def other_process(child_conn):
    print 'other_process'
    global SCREENRECT

    pygame.init()
    SCREENRECT = Rect((0, 0),
        (640, 480))
    screen = set_mode(SCREENRECT.size)
    set_caption('test_mp')

    background = pygame.Surface(screen.get_size())  # и ее размер
    background = background.convert()
    background.fill((100, 100, 0,))  # заполняем цветом
    screen.blit(background, (0, 0))
    pygame.display.flip()
    time.sleep(randint(1,5))
    objects_state = None
    while child_conn.poll(0):
        # данные есть - считываем все что есть
        objects_state = child_conn.recv()
        time.sleep(randint(1,5))
    print 'other process recieved', objects_state
    time.sleep(randint(1,5))
    child_conn.send('preved')
    print 'other process sended'


parent_conn, child_conn = Pipe()

p = Process(target=other_process, args=(child_conn, ))
print 'maked'
p.start()
print 'started'
time.sleep(randint(1,5))
ui_state = False
while parent_conn.poll(0):
    # состояний м.б. много, оставляем только последнее
    ui_state = parent_conn.recv()
    time.sleep(randint(1,5))
print 'recieved', ui_state
parent_conn.send('medved')
print 'sended'

p.join()
print 'joined'
