"""
XXX
"""

from happy.registry import Registry
from happy.registry import TypeAxis

class Events(object):
    def __init__(self, registry=None):
        if registry is None:
            registry = Registry(('type', TypeAxis()))

    def register(self, listener, event_type):
        listeners = self.registry.lookup(event_type)
        if event_type is None:
            listeners = []
            self.registry.register(listeners, event_type)
        listeners.append(listener)

    def notify(self, event):
        listeners = self.registry.lookup(event)
        for listener in listeners(
