
class Route(object):
    def __init__(self, target, path):
        route = []
        variable_indices = []
        for i, element in enumerate(filter(None, path.split('/'))):
            path_element = _PathElement(element)
            if path_element.variable:
                variable_indices.append(i)
            route.append(path_element)

        self.target = target
        self.path = path
        self.route = route
        self.variable_indices = variable_indices

class _PathElement(object):
    def __init__(self, element):
        if element.startswith(':'):
            self.variable = True
            self.name = element[1:]
        else:
            self.variable = False
            self.name = element

class RoutesDispatcher(object):
    def __init__(self):
        self._map = _MapNode()

    def add_route(self, target, path):
        route = Route(target, path)
        map_node = self._map
        for element in route.route:
            if element.variable:
                key = ':'
            else:
                key = element.name

            if not map_node.has_key(key):
                map_node[key] = _MapNode()

            map_node = map_node[key]

        map_node.route = route

    def match(self, path):
        elements = filter(None, path.split('/'))
        route = self._match(self._map, elements)
        if route is None:
            return None

        args = []
        kwargs = {}
        for index in route.variable_indices:
            name = route.route[index].name
            if name:
                kwargs[name] = elements[index]
            else:
                args.append(elements[index])

        return route, args, kwargs

    def _match(self, map_node, elements):
        if not elements:
            return map_node.route

        next_node = None
        element = elements[0]
        next_node = map_node.get(element, None)
        if next_node is None:
            next_node = map_node.get(':', None)
        if next_node is None:
            return None
        return self._match(next_node, elements[1:])

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

        # Call target
        route, args, kwargs = match
        return route.target(request, *args, **kwargs)

class _MapNode(dict):
    route = None
