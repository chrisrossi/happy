"""
XXX
"""
from happy.registry import Registry
from happy.registry import SimpleAxis
from happy.registry import TypeAxis

class AdaptationManager(object):
    """
    XXX
    """
    def __init__(self, registry=None):
        if registry is None:
            registry = Registry(
                ('from_type', TypeAxis()),
                ('to_type', SimpleAxis()),
            )
        self.registry = registry

    def register(self, adapter, from_type, to_type):
        self.registry.register(adapter, from_type, to_type)

    def adapt(self, obj, to_type):
        adapter = self.registry.lookup(obj, to_type)
        if adapter is None:
            raise KeyError("No adapter from %s to %s" % (type(obj), to_type))
        return adapter(obj)
