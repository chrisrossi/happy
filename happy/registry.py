"""
Generic notion of registry.  Fundamentally a registry is just a way to store
some object with a set of associations and then look up that object later.
An example use case might be registering view functions for a web framework
that are looked up by the type of the object being viewed.  Or an event system
might use a registry to look up event handlers by type of event.

This registry, as it is meant to support a wide range of uses cases
generically, is, by necessity, quite abstract.  Generally users of this module
will wrap a registry with some sort of domain specific API such that
registrations can be made using an API that makes clear what is being
registered and how it is being retrieved.

A registry is created with an ordered set of N named axes, where an axis is,
basically, something by which you can look up an object.  Objects can be
registered with 0 to N axes.  Object lookups can, likewise, be looked up
according to any subset of axes in the registry--only objects registered with
the same set of axes, though, will be found.

This registry supports a notion called 'specificity' whereby registrations can
either be more or less specific, with more specific registrations taking
precedence on lookup.  To think about this consider a registry with a single
`TypeAxis`.  A `TypeAxis` allows a lookup to be performed according to some
object's type.  Let's say we wanted to make a general, catch all, registration
that we know will apply to any object::

    from happy.registry import Registry
    from happy.registry import TypeAxis
    registry = Registry(('type', TypeAxis()))
    registry.register(default_view, type=object)

If only the above registration is made, any lookup will result in
`default_view` being returned, since all object types inherit from object::

    blog_post = BlogPost()
    view = registry.lookup(blog_post)  # default_view

We could, of course, make a more specific registration::

    registry.register(blog_post_view, type=BlogPost)
    view = registry.lookup(blog_post) # Now returns blog_post_view

The registration for type `BlogPost` type is more specific than the
registration for the `object` type, so lookups on objects of type BlogPost
will return the blog_post_view, whereas all other objects will return the
default_view.  Specificity is applied (or not applied) by individual axes.

XXX Todo Explain left to right ordering when searching axes and interaction
with specificity.

An axis object implements a basic interface comprised of one method::

interface Axis: def matches(obj, keys): ''' For a given object, `obj`, return
the subset of keys which match this object in this axis, in order from most to
least specific. ''' The `SimpleAxis` class included in this module implements
the most basic axis possible--one that effectively acts like a dictionary,
where the object is the key to the axis. It also provides a means of creating
axis classes by means of what might be a more intuitive override. The
`get_keys` simply returns keys used for lookup in the axis for a given
object and is a convenient override point.
"""
# XXX Everything written in English here currently blows.  Find a way to
#     explain this better.

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

        # Trim empty tail nodes for faster look ups
        while aligned and aligned[-1] is None:
            del aligned[-1]

        return aligned

class _TreeNode(dict):
    target = None

class SimpleAxis(object):
    """
    A simple axis where the key into the axis is the same as the object to be
    matched (aka the identity axis). This axis behaves just like a dictionary.
    You might use this axis if you are interested in registering something by
    name, where you're registering an object with the string that is the name
    and then using the name to look it up again later.

    Subclasses can override the 'get_keys' method for implementing arbitrary
    axes.
    """
    def matches(self, obj, keys):
        for key in self.get_keys(obj):
            if key in keys:
                yield key

    def get_keys(self, obj):
        """
        Return the keys for the given object that could match this axis, from
        most specific to least specific.  A convenient override point.
        """
        return [obj,]

class TypeAxis(SimpleAxis):
    """
    An axis which matches the class and super classes of an object in method
    resolution order.
    """
    def get_keys(self, obj):
        return type(obj).mro()
