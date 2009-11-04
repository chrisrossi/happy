"""
Handles the notion of dispatching to a view (aka controller) based on traversal
of an object graph.
"""

from happy.registry import Registry
from happy.registry import MROAxis
from happy.registry import IdentityAxis

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
    """
    def __init__(self, root_factory, registry=None):
        self.root_factory = root_factory
        if registry == None:
            registry = Registry(MROAxis(), IdentityAxis())
        self.registry = registry

    def __call__(self, request):
        root = self.root_factory(request)
        context, subpath = traverse(root, request.path_info)
        controller = self._lookup_controller(context, request, subpath)
        if controller is not None:
            return controller(context, request)

    def _lookup_controller(self, context, request, subpath):
        """
        Specifically put here as an override point for subclasses that might
        want to do something different to find a controller for a specific
        context.
        """
        if subpath:
            return self.registry.lookup(context, subpath[0])
        return self.registry.lookup(context)
