"""
Generic notion of registry. A registry is used by other components to track
registrations of components. Fundamentally a registry is just a way to store
some object with a set of associations and then look up that object later. A
graph traversal dipatcher, for example, might use a registry to associate
controllers with context types, in order to call view code based on the type
of a content object. Alternatively, an event system might use a registry to
register handlers for events.

An object is registered by means of axes, where an axis is, essentially, a key
for look up. A registry must be initialized with one or more axes. An axis is
a callable which accepts an object as an argument and returns a key to be used
as a lookup key for that axis. The simplest axis would be the identity axis,
which simply returns the object itself::

    identity_axis = lambda obj: obj

The returned value must be hashable, as it is used in a dictionary look up.
An axis may, optionally, have an attribute, ``specificity``, which, if
``True``, implies that the return value will, rather than a single value,
be a list of hashable key values in order of most specific to least
specific.  The notion of specificity is somewhat artificial and context
dependent, but allows the creation of axes that can perform lookups based
on an inheritance chain.  An example is an axis for class MRO (Method
Resolution Order)::

    class MROAxis(object):
        specificity = True

        def __call__(self, obj):
            return type(obj).mro()

Suppose the following classes::

    class C(object):
       pass

    class D(C):
        pass

    class E(C):
        pass

Using an MRO axis, you could register a target for C, which would match
instances of C, D, or E.  If you then made a more specific registration by
registering a different target for D, then instances of D would then start
getting back the more specific target, whereas instances of C or E would still
get the target registered for C.

Both an identity axis and an MRO axis are available for import from this
package::

    from happy.registry import identity_axis
    from happy.registry import mro_axis

A registry is instantiated by passing the axes to use as arguments::

    from happy.registry import Registry

    registry = Registry(mro_axis, identity_axis)

The ``register`` method is used to add targets to the registry::

    registry.register(target1, C)
    registry.register(target2, C, 'kittens')
    registry.register(target3, D)

The first argument is the target to return from a lookup.  The next arguments
correspond to the axes used to instantiate the registry.  The ``lookup`` method
is then used to retrieve objects from the registry:

    foo = C()
    target1 = registry.lookup(foo)
    target2 = registry.lookup(foo, 'kittens')
    bar = D()
    target3 = registry.lookup(bar)
    target2 = registry.lookup(foo, 'kittens')

Lookups only match registrations on the same number of axes as the lookup.
Hence, the fourth lookup above returns target2 and not target3.
"""

class Registry(object):
    """
    Implements registry.  See module level documentation.
    """
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
        keys = map(lambda x: x[0](x[1]), zip(self.axes, objs))

        return self._lookup(map_node, self.axes, keys)

    def _lookup(self, map_node, axes, keys):
        if not keys:
            return getattr(map_node, 'target', None)

        axis, key = axes[0], keys[0]
        if getattr(axis, 'specificity', False):
            for k in key:
                if k in map_node:
                    target = self._lookup(map_node[k], axes[1:], keys[1:])
                    if target is not None:
                        return target

        elif key in map_node:
            return self._lookup(map_node[key], axes[1:], keys[1:])

        return None


class _MapNode(dict):
    target = None


class MROAxis(object):
    specificity = True

    def __call__(self, obj):
        return type(obj).mro()


mro_axis = MROAxis()
identity_axis = lambda x: x
