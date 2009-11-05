"""
Generic notion of registry. A registry is used by other components to track
registrations of components. Fundamentally a registry is just a way to store
some object with a set of associations and then look up that object later. A
graph traversal dipatcher, for example, might use a registry to associate
controllers with context types, in order to call view code based on the type
of a content object. Alternatively, an event system might use a registry to
register handlers for events.
"""
import copy

class Registry(object):
    def __init__(self, *axes):
        self._registry = _MapNode()
        self.axes = axes

    def register(self, target, *keys):
        if len(keys) > len(self.axes):
            raise ValueError("Can't register more keys than there are axes.")

        map_node = self._registry
        for key in keys:
            if not map_node.has_key(key):
                map_node[key] = _MapNode()
            map_node = map_node[key]
        map_node.target = target

    def lookup(self, *objs):
        if len(objs) > len(self.axes):
            raise ValueError("Can't look up more keys than there are axes.")

        map_node = self._registry
        keys = map(lambda x: x[0].get_key(x[1]), zip(self.axes, objs))

        return self._lookup(map_node, list(self.axes), copy.copy(keys))

    def _lookup(self, map_node, axes, keys):
        if not keys:
            return getattr(map_node, 'target', None)

        axis, key = axes.pop(0), keys.pop(0)
        if axis.specificity:
            for k in key:
                if k in map_node:
                    target = self._lookup(map_node[k],
                                          copy.copy(axes), copy.copy(keys))
                    if target is not None:
                        return target

        elif key in map_node:
            return self._lookup(map_node[key], axes, keys)

        return None

class IAxis(object):
    """
    Class which implement ``IAxis`` define an axis used for registration and
    lookup in a registry.
    """
    specificity = property(
        doc="""A boolean attribute indicating whether or not this axis supports
               the notion of specificity.  If ``True``, the keys returned by
               ``get_key`` for this axis must be iterables yielding individual
               hashable keys in decreasing order of specificity.  Lookups will
               be performed on each key in turn until a match is found.  If
               ``False``, then ``get_key`` is assumed to return a simple
               hashable key which will be used to perform a single lookup on
               the axis."""
    )

    def get_key(self, obj):
        """
        Gets key for a given object.  Key is used to perform a registry lookup
        on this axis.  If axis uses specificity, returns an iterable of
        individual hashable keys, in decreasing order order of specificy, which
        are tried in turn until a match is found.  If axis does not use
        specificity, returns a single hashable key used for a lookup in this
        axis.
        """

class MROAxis(object):
    specificity = True

    def get_key(self, obj):
        return obj.__class__.mro()

class IdentityAxis(object):
    specificity = False

    def get_key(self, obj):
        return obj



class _MapNode(dict):
    target = None
