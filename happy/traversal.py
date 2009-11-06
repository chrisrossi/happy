"""
This module provides tools for dispatching to controllers based on traversal of
an object graph.  The object graph is populated with the data objects, called
models, that are exposed by your web site.  The graph has a tree structure
which maps onto the url being requested.  Each model object represents the
content you want to expose via your web site.

Consider, for illustration purposes, the following classes::

    class Folder(dict):
        pass

    class Cat(object):
        pass

    class Dog(object):
        pass

Now let's presume instances of these classes have been stored somewhere and
composed into following object graph::

    root = Folder()
    cats = root['cats'] = Folder()
    lily = cats['lily'] = Cat()
    ginger = cats['ginger'] = Cat()
    dogs = root['dogs'] = Folder()
    elsa = dogs['elsa'] = Dog()
    nemo = dogs['nemo'] = Dog()

The following urls would then map onto the above objects::

    /            (root folder)
    /cats/       (cats folder)
    /cats/lily   (lily cat)
    /dogs/elsa   (elsa dog)

The object graph and corresponding url space represent a natural containment
hierarchy and is an intuitive way to organize content in content management
type applications, where content can be organized in arbitrarily nested
structures.

Traversal of the object hierarchy is done using only the ``__getitem__`` method
of model objects.  A model which has the ``__getitem__`` method is a container
and may contain other models.  A model without the ``__getitem__`` method is,
necessarily, a leaf node.  This is the only contract expected of models in
order to be traversable.

In order for anything interesting to happen, models must be mapped to
conrollers in some way. For information on mapping models to controllers, see
the ``TraversalDispatcher`` class.

"""

from happy.registry import Registry
from happy.registry import mro_axis
from happy.registry import identity_axis

def traverse(root, path):
    """
    Traverses object graph starting at ``root`` using ``path``.  Returns the
    tuple: ``(context, subpath)`` where ``context`` is the object found
    as a result of the traversal and ``subpath`` is a list of the path
    segments that were not used by the traversal, ie the path segements which
    follow the segment that corresponds to the context.
    """
    path = filter(None, path.split('/'))
    node = root
    while path:
        if not hasattr(node, '__getitem__'):
            break

        next = path.pop(0)
        try:
            node = node.__getitem__(next)
        except KeyError:
            path.insert(0, next)
            break

    return node, path

class TraversalDispatcher(object):
    """
    XXX
    """
    def __init__(self, root_factory, registry=None):
        self.root_factory = root_factory
        if registry == None:
            registry = Registry(mro_axis, identity_axis)
        self.registry = registry

    def __call__(self, request):
        root = self.root_factory(request)
        context, subpath = traverse(root, request.path_info)
        controller = self._lookup_controller(context, request, subpath)
        if controller is not None:
            return controller(context, request)

    def _lookup_controller(self, context, request, subpath):
        """
        XXX
        """
        if subpath:
            return self.registry.lookup(context, subpath[0])
        return self.registry.lookup(context)
