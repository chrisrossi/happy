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
        self._tree = _TreeNode()
        self._axes = [axis for name, axis in axes]
        self._axes_dict = dict([
            (name, (i, axis)) for i, (name, axis) in enumerate(axes)
        ])

    def register(self, target, *arg_keys, **kw_keys):
        self._register(target, self._align_with_axes(arg_keys, kw_keys), False)

    def override(self, target, *arg_keys, **kw_keys):
        self._register(target, self._align_with_axes(arg_keys, kw_keys), True)

    def _register(self, target, keys, override):
        tree_node = self._tree
        for key in keys:
            if not tree_node.has_key(key):
                tree_node[key] = _TreeNode()
            tree_node = tree_node[key]

        if not (override or tree_node.target is None):
            raise ValueError(
                "Registration conflicts with existing registration.  Use "
                "override method to override."
            )

        tree_node.target = target

    def lookup(self, *arg_objs, **kw_objs):
        objs = self._align_with_axes(arg_objs, kw_objs)
        axes = self._axes
        return self._lookup(self._tree, objs, axes)

    def _lookup(self, tree_node, objs, axes):
        """
        Recursively traverse registration tree, from left to right, most
        specific to least specific, returning the first target found on a
        matching node.
        """
        if not objs:
            return tree_node.target

        obj = objs[0]

        # Skip non-participating nodes
        if obj is None:
            next_node = tree_node.get(None, None)
            if next_node is not None:
                return self._lookup(next_node, objs[1:], axes[1:])
            return None

        # Get matches on this axis and iterate from most to least specific
        axis = axes[0]
        for match_key in axis.matches(obj, tree_node.keys()):
            target = self._lookup(tree_node[match_key], objs[1:], axes[1:])
            if target is not None:
                return target

        return None

    def _align_with_axes(self, args, kw):
        """
        Create a list matching up all args and kwargs with their corresponding
        axes, in order, using 'None' as a placeholder for skipped axes.
        """
        axes_dict = self._axes_dict
        aligned = [None for i in xrange(len(axes_dict))]

        args_len = len(args)
        if args_len + len(kw) >  len(aligned):
            raise ValueError('Cannot have more arguments than axes.')

        for i, arg in enumerate(args):
            aligned[i] = arg

        for k, v in kw.items():
            i_axis = axes_dict.get(k, None)
            if i_axis is None:
                raise ValueError('No axis with name: %s' % k)

            i, axis = i_axis
            if aligned[i] is not None:
                raise ValueError('Axis defined twice between positional and '
                                 'keyword arguments')

            aligned[i] = v

        # Trim empty tail nodes, for somewhat faster look ups
        while aligned and aligned[-1] is None:
            del aligned[-1]

        return aligned

class _TreeNode(dict):
    target = None

class BaseAxis(object):
    """
    Provides a convenient base with abstract methods to be overridden by axis
    implementations. Provides a good, basic implementation of 'matches' that
    is factored to include most common cases. More complex algorithms should
    probably just implement their own class from the ground up.
    """
    def matches(self, obj, keys):
        for key in self.get_keys(obj):
            if key in keys:
                yield key

    def get_keys(self, obj):
        """
        For a given object, return an iteratable of the keys that can possibly
        be used to match this object in the axis, from most specific to least
        specific.
        """
        raise NotImplementedError("Must be implemented by concrete subclass.")

class SimpleAxis(BaseAxis):
    """
    A simple axis where the key into the axis is the same as the object to be
    matched (aka the identity axis). This axis behaves just like a dictionary.
    You might use this axis if you are interested in registering something by
    name, where you're registering an object with the string that is the name
    and then using the name to look it up again later.
    """
    def get_keys(self, obj):
        return [obj,]

class TypeAxis(BaseAxis):
    """
    An axis which matches the class and super classes of an object in method
    resolution order.
    """
    def get_keys(self, obj):
        return type(obj).mro()
