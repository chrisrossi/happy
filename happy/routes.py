"""
This package provides a fairly simplified implementation of so called "routes"
based dispatch. This is based loosely on the style of dispatch used by Pylons,
Ruby on Rails, BFG and others.
"""
import inspect
import webob

class RoutesDispatcher(object):
    """
    The ``RoutesDispatcher`` class provides URL based dispatch based on
    ``routes`` that are registered on the dispatcher.  Each route is registered
    to call a single controller.  The call signature of controller may be
    either::

      controller(request)

    or::

      controller(request, **kw)

    In the second form, ``**kw`` is filled in with match elements from the
    route. In either form the parameters of the matching route are also passed
    as the ``match_dict`` attribute of request. A route is added via the
    ``register`` method::

      from happy.routes import RoutesDispatcher
      dispatcher = RoutesDispatcher()
      dispatcher.register(controller, '/foo/:animal')

    The above route matches any two segment path that begins with 'foo'. These
    urls match::

      /foo/12
      /foo/cat
      /foo/horse/

    These urls do not match::

      /bar/foo/12
      /foo/12/cat

    When matched, the controller for this route will be called with a request
    object and a single keyword argument for the match element::

      def controller(request, animal):
          pass

    Or you might maintain the simpler call signature and query the request's
    ``match_dict`` to get the value of animal::

      def controller(request):
          animal = request.match_dict['animal']

    An asterisk, `*`, may optionally appear at the end of any route and matches
    zero or more arbitrary path segments::

      dispatcher.register(controller, 'animal', '/foo/:animal/*')

    This will match any path that starts with '/foo' and contains at least one
    more arbitrary path element, which will be assigned to the match variable
    `animal`.  Any segments following the first two are considered the
    `subpath` and will be assigned to the ``subpath`` attribute of request.

    In some cases more than one route may match a particular url.  In these
    cases, the more specific registration wins.  Consider these two
    registrations::

      dispatcher.register(controller1, 'animal', '/foo/:animal/*')
      dispatcher.register(controller2, 'foobar', '/foo/bar/*')

    In this case, the path `/foo/goose/one` will be dispatched to controller1
    while `/foo/bar/two` will be dispatched to controller2.

    When calling the target controller for a route, the dispatcher will create
    new copy of the request object and then, optionally, rewrite the
    `script_name` and `path_info` attributes such that the target controller
    is called as though it were a stand alone application (which it very well
    could be). The default behavior is to not rewrite `script_name` and
    `path_info`. To enable rewriting, pass a value of `True` to the
    `rewrite_paths` parameter of the class constructor. When rewriting is
    enabled, the portion of the url path consumed by the route will be
    appended to the end of `script_name` and the `subpath` will become the new
    `path_info`. The following code illustrates::

      dispatcher.register(controller, 'animals', '/foo/:animal/*')

      # Let's say our dispatcher is at the root of our site (ie, script_name is
      # empty) and is then called with a path_info of /foo/cat/tiger/lily
      def controller(request):
          assert request.script_name == '/foo/cat'
          assert request.path_info == '/tigery/lily'
          return webob.Response("It's a %s" % request.match_dict['animal'])

      request = webob.Request.blank('/foo/cat/tiger/lily')
      assert request.script_name == ''
      assert request.path_info == '/foo/cat/tiger/lily'

      dispatcher(request)
    """
    Request = webob.Request # Request factory is overridable

    def __init__(self, rewrite_paths=False):
        self._tree = _TreeNode()
        self._routes_by_name = {}
        self.rewrite_paths = rewrite_paths

    def register(self, target, name, path):
        return self._register(target, name, path, False)

    def override(self, target, name, path):
        return self._register(target, name, path, True)

    def _register(self, target, name, path, override):
        route = Route(self._wrap_callable(target), path)
        tree_node = self._tree
        for element in route._route:
            if element.variable:
                key = ':'
            else:
                key = element.name

            if not tree_node.has_key(key):
                tree_node[key] = _TreeNode()

            tree_node = tree_node[key]

        if not override and tree_node.route is not None:
            raise ValueError(
                "A target has already been registered for this route.  "
                "Use override to replace this route's target."
            )

        tree_node.route = route
        self._routes_by_name[name] = route
        return route

    def __getitem__(self, name):
        return self._routes_by_name[name]

    def match(self, path):
        elements = filter(None, path.split('/'))
        match = self._match(self._tree, [], elements)
        if match is None:
            return None

        route, consumed, subpath = match
        args = {}
        for index in route._variable_indices:
            name = route._route[index].name
            args[name] = elements[index]

        return route, consumed, subpath, args

    def _match(self, tree_node, consumed, subpath):
        if not subpath:
            if tree_node.route is not None:
                return tree_node.route, consumed, subpath
            if '*' in tree_node:
                return tree_node['*'].route, consumed, subpath
            return None

        next_node = None
        element = subpath[0]
        next_node = tree_node.get(element, None)
        if next_node is None:
            next_node = tree_node.get(':', None)
        if next_node is None:
            if '*' in tree_node:
                return tree_node['*'].route, consumed, subpath
            return None
        return self._match(next_node, consumed + [element], subpath[1:])

    def __call__(self, request, path=None):
        # Allow path to be called in, in case we don't want to start matching
        # at the root of the request's path_info.  (Or for some reason we don't
        # want to match on the request's path_info at all.)
        if path is None:
            path = request.path_info

        # Look up the route, return None if no match
        match = self.match(path)
        if match is None:
            return None

        route, consumed, subpath, args = match

        # Make new copy of request, so our decorations don't leak outside of
        # this dispatcher.
        original_request = request
        request = self.Request(request.environ.copy())

        # Optionally, rewrite script_name and path_name
        if self.rewrite_paths:
            script = request.script_name.split('/')
            request.script_name = '/'.join(script + consumed)

            path_info = '/'.join([''] + subpath)
            if path.endswith('/'):
                if path_info:
                    path_info += '/'
                else:
                    request.script_name += '/'
            request.path_info = path_info

        # Decorate request
        request.subpath = subpath
        request.match_dict = args
        request.route = route
        request.request = original_request

        # Call target
        return route.target(request, **args)

    def _wrap_callable(self, controller):
        def request_only_signature(request, **args):
            return controller(request)

        if inspect.isfunction(controller):
            func = controller
        else:
            func = controller.__call__

        args, varargs, keywords, defaults = inspect.getargspec(func)
        if args == ['request'] and not(varargs or keywords or defaults):
            return request_only_signature
        return func

class Route(object):
    def __init__(self, target, path):
        route = []
        variable_indices = []
        wildcard = False
        for i, element in enumerate(filter(None, path.split('/'))):
            if wildcard:
                raise ValueError('Wildcard must come at end of path')

            path_element = _PathElement(element)
            if path_element.variable:
                variable_indices.append(i)
            route.append(path_element)
            wildcard = path_element.wildcard

        self.target = target
        self.path = path
        self._route = route
        self._variable_indices = variable_indices

    def url(self, request, **match_dict):
        subpath = match_dict.pop('subpath', None)
        path_info = []
        for element in self._route:
            if element.variable:
                path_info.append(match_dict[element.name])
            elif element.wildcard:
                if subpath is not None:
                    path_info += subpath
            else:
                path_info.append(element.name)

        path_info = '/' + '/'.join(path_info)
        if self.path.endswith('/') or (
            self.path.endswith('*') and not subpath):
            path_info += '/'

        return request.application_url.rstrip('/') + path_info

class _PathElement(object):
    wildcard = False
    variable = False

    def __init__(self, element):
        if element.startswith(':'):
            self.variable = True
            self.name = element[1:]
        elif element == '*':
            self.wildcard = True
            self.name = '*'
        else:
            self.name = element

class _TreeNode(dict):
    route = None
