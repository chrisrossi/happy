"""
XXX
"""
from happy.registry import Registry
from happy.registry import identity_axis
from happy.registry import mro_axis

class AdaptationManager(object):
    """
    XXX
    """
    def __init__(self, registry=None):
        if registry is None:
            registry = Registry(mro_axis, identity_axis)
        self.registry = registry

    def register(self, adapter, from_type, to_type):
        self.registry.register(adapter, from_type, to_type)

    def adapt(self, obj, to_type):
        adapter = self.registry.lookup(obj, to_type)
        if adapter is None:
            raise KeyError("No adapter from %s to %s" % (type(obj), to_type))
        return adapter(obj)
