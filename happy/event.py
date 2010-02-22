"""
XXX
"""

from happy.registry import Registry
from happy.registry import TypeAxis

class EventManager(object):
    def __init__(self):
        self._registry = {}

    def register(self, event_type, listener):
        registry = self._registry
        listeners = registry.get(event_type, None)
        if listeners is None:
            registry[event_type] = listeners = []
        listeners.append(listener)

    def unregister(self, event_type, listener):
        registry = self._registry
        listeners = registry.get(event_type, None)
        if listeners is not None:
            try:
                listeners.remove(listener)
                if not listeners:
                    del registry[event_type]
                return
            except ValueError:
                pass # Thrown by listeners.remove if listener is not in list
        raise ValueError("Listener %s is not registered for %s" %
                         (listener, event_type))

    def notify(self, event):
        for listener in self.get_listeners(type(event)):
            listener(event)

    def get_listeners(self, event_type):
        registry = self._registry
        all_listeners = []
        for t in event_type.mro():
            if t in registry:
                all_listeners += registry[t]

        return all_listeners
