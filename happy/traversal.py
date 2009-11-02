"""
Handles the notion of dispatching to a view (aka controller) based on traversal
of an object graph.
"""

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
