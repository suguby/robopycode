# -*- coding: utf-8 -*-
from robogame_engine.events import GameEvent


class EventGunReloaded(GameEvent):

    def handle(self, obj):
        obj.on_gun_reloaded()


class EventTargetDestroyed(GameEvent):

    def handle(self, obj):
        obj.on_target_destroyed()


class EventHit(GameEvent):

    def handle(self, obj):
        obj.on_hitted()


class EventRadarDetect(GameEvent):

    def handle(self, obj):
        obj.on_radar_detect(self._event_objs)



