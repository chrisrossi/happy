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
    An instance of ``TraversalDispatcher`` dispatches a request to a controller
    by traversing an object graph to find a model that is the ``context`` and
    then looking up a controller for that context and calling it.  Traversal
    is performed by the ``traverse`` function in the same module.  Controllers
    (aka 'views' in some systems) have the following signature::

        controller(request, context)

    Where context is the result of the traversal.  Controllers are registered
    by type (class) and optionally, a controller name.  If the result of
    calling ``traverse`` returns a non-empty subpath, the first element of the
    subpath is considered to be the controller name and a controller is looked
    up based on the type of the context and controller name.  If there is no
    controller name, a controller is looked up by context type only.  Consider
    this example::

        def root_factory(request):
            return my_object_graph_root

        from happy.traversal import TraversalDispatcher
        dispatcher = TraversalDispatcher(root_factory)
        dispatcher.register(show_cat_controller, Cat)
        dispatcher.register(edit_cat_controller, Cat, 'edit.html')

    The first registration will cause the 'show_cat_controller' to be used for
    any instance of Cat or a subclass.  The second registration will instead
    use an edit view, if the result of traversal yields a controller name of
    'edit.html'.  So if this URL maps to a Cat instance, it will be handled
    using the 'show_cat_controller':

        http://example.com/foo/cats/ginger

    This URL will instead be handled by the 'edit_cat_controller'::

        http://example.com/foo/cats/ginger/edit.html

    Internally, ``TraversalDispatcher`` uses an instance of
    ``happy.registry.Registry`` with an ``mro axis`` and ``identity axis``,
    for the type and controller name respectively. The constructor for
    ``TraversalDispatcher`` accepts an optional `registry` argument, which
    will cause it to use the passed in registry rather than create its own.
    This is potentially useful if you want to share a registry with another
    component or compose registrations in another part of your code. This can
    also be used to change how controllers are looked up for a context, but
    this is usually not useful without also subclassing
    ``TraversalDispatcher``.

    For advanced users that want to subsitute their own means of looking up
    controllers for a context, ``TraversalDispatcher`` is designed to be
    subclassed.  Overriding the ``_lookup_controller`` method, a subclass can
    substitute whole scale its own logic for looking up controllers.  Assuming
    a subclass still uses a registry, you might want to also override the
    ``register`` method if the axes used by the registry don't align with the
    defaults.

    There is not a lot of code in this class, so another perfectly valid
    approach is to simply cut and paste the code and customize at will.
    """
    def __init__(self, root_factory, registry=None):
        self.root_factory = root_factory
        if registry == None:
            registry = Registry(mro_axis, identity_axis)
        self._registry = registry

    def __call__(self, request):
        root = self.root_factory(request)
        context, subpath = traverse(root, request.path_info)
        controller = self._lookup_controller(request, context, subpath)
        if controller is not None:
            return controller(request, context)

    def register(self, controller, klass, name=None):
        if name is None:
            self._registry.register(controller, klass)
        else:
            self._registry.register(controller, klass, name)

    def _lookup_controller(self, request, context, subpath):
        if subpath:
            return self._registry.lookup(context, subpath[0])
        return self._registry.lookup(context)
