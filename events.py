#!/usr/bin/env python
# -*- coding: utf-8 -*-


class GameEvent:
    """
        Base class for objects events
    """

    def __init__(self, event_objs=None):
        self._event_objs = event_objs or []

    def get_event_objects(self):
        return self._event_objs


class EventBorn(GameEvent):

    def handle(self, obj):
        obj.born()


class EventStopped(GameEvent):

    def handle(self, obj):
        obj.stopped()


class EventStoppedAtTargetPoint(GameEvent):

    def handle(self, obj):
        obj.stopped_at_target_point(self._event_objs)


class EventGunReloaded(GameEvent):

    def handle(self, obj):
        obj.gun_reloaded()


class EventCollide(GameEvent):

    def handle(self, obj):
        obj.collided_with(self._event_objs)


class EventHit(GameEvent):

    def handle(self, obj):
        obj.hitted()


class EventTargetDestroyed(GameEvent):

    def handle(self, obj):
        obj.target_destroyed()


class EventRadarRange(GameEvent):

    def handle(self, obj):
        obj.in_tank_radar_range(self._event_objs)

class EventHearbeat(GameEvent):

    def handle(self, obj):
        obj.hearbeat()
