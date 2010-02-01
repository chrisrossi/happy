"""
A view is a responder which models some representation of an object and/or
allows an object to be mutated. The object on which a view acts is known as
the 'context'. The view itself is a callable with one or the other of these
signatures::

    def view(request, context):
        '''
        The context object is passed in as an argument.
        '''

    def view(request):
        '''
        The context object is an attribute of the request.
        '''
        context = request.context

Happy dispatchers which might dispatch to views know about both signatures
and can figure out how to call a particular view appropriately.
"""

from happy.registry import Registry
from happy.registry import SimpleAxis
from happy.registry import TypeAxis

class ViewRegistry(Registry):
    """
    A registry which allows registration and lookup of views based on the
    type of the context object, certain aspects of the HTTP request, and/or
    a view name.
    """
    def __init__(self):
        super(ViewRegistry, self).__init__(
            ('request', _PredicatesAxis()),
            ('context', TypeAxis()),
            ('name', SimpleAxis()),
        )

    def register(self, view, context_type=None, name=None, **predicates):
        """
        Arguments::

          `view`: The view callable.
          `context_type`: The class of the context for this view.
          `name`: Optionally, a name for this view--for further discriminating.

        The `predicates` are all derived from a request object and can be any
        of the following:

          `request_method`: GET, POST, etc...
          `request_param`: Name of a request parameter that must be present to
                           match, or 'name=value' expression where request
                           parameter, name, must be present and match value.
          `xhr`: True or False.  For True, there must be an X-Requested-With
                 header which equals 'XMLHttpRequest'.

           XXX More to come.
        """
        super(ViewRegistry, self).register(
            view, _Predicates(predicates), context_type, name
        )

    def lookup(self, request, context, name=None):
        # Presents a domain specific method signature, but otherwise just calls
        # Registry.lookup()
        return super(ViewRegistry, self).lookup(request, context, name)


class _PredicatesAxis(object):
    def matches(self, request, keys):
        keys = list(keys) # copy

        # Sort by number of predicates
        keys.sort(key=lambda x: len(x), reverse=True)

        # More predicates is more specific
        # XXX Match order for same number of predicates is undefined.
        for predicates in keys:
            if predicates.match(request):
                yield predicates


class _Predicates(dict):
    known_predicates = set([
        'request_method',
        'request_param',
        'xhr',
    ])

    def __init__(self, d): # Initialize from dict
        for k in d:
            if k not in self.known_predicates:
                raise ValueError('Unkown predicate: %s' % k)
        super(_Predicates, self).__init__(d)

    def __hash__(self):
        h = 0
        for k, v in self.items():
            h += hash((k,v))
        return h

    def match(self, request):
        for name, value in self.items():
            matcher = getattr(self, '_match_%s' % name)
            if not matcher(request, value):
                return False
        return True

    def _match_request_method(self, request, value):
        return request.method == value

    def _match_request_param(self, request, param):
        if '=' in param:
            name, value = param.split('=')
            return request.params.get(name, None) == value
        return param in request.params

    def _match_xhr(self, request, value):
        xrw = request.headers.get('X-Requested-With', None)
        return (xrw == 'XMLHttpRequest') == value
