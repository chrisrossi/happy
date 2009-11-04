import unittest

class TraversalTests(unittest.TestCase):
    def test_traverse(self):
        from happy.traversal import traverse as f
        root = DummyModel()
        a = root['a'] = DummyModel()
        b = root['b'] = DummyModel()
        c = b['c'] = DummyModel()
        d = a['d'] = object()
        e = root['e'] = DummyModel()
        g = e['g'] = DummyModel()
        h = e['h'] = DummyModel()

        self.assertEqual(f(root, ''), (root, []))
        self.assertEqual(f(root, '/'), (root, []))
        self.assertEqual(f(root, '/a'), (a, []))
        self.assertEqual(f(root, '/a/'), (a, []))
        self.assertEqual(f(root, '/a/d/f'), (d, ['f']))
        self.assertEqual(f(root, '/b/c'), (c, []))
        self.assertEqual(f(root, '/b/c/d/e'), (c, ['d', 'e']))
        self.assertNotEqual(f(root, '/e/g'), (h, []))

class TraversalDispatcherTests(unittest.TestCase):
    def test_default_view(self):
        root = DummyModel()
        root_factory = lambda request: root
        from happy.traversal import TraversalDispatcher
        dispatcher = TraversalDispatcher(root_factory)
        calls = []
        def view(context, request):
            calls.append((context, request))
        registry = dispatcher.registry
        registry.register(view, DummyModel)
        from webob import Request
        request = Request.blank('/')
        dispatcher(request)
        self.assertEqual(calls[0], (root, request))

    def test_named_view(self):
        root = DummyModel()
        root_factory = lambda request: root
        from happy.traversal import TraversalDispatcher
        dispatcher = TraversalDispatcher(root_factory)
        calls = []
        def view(context, request):
            calls.append((context, request))
            return 'Hello'

        registry = dispatcher.registry
        registry.register(view, DummyModel, 'hello')
        from webob import Request
        response = dispatcher(Request.blank('/'))
        self.assertEqual(response, None)
        response = dispatcher(Request.blank('/hello'))
        self.assertEqual(response, 'Hello')

class DummyModel(dict):
    def __eq__(self, other):
        return self is other

class DummyModelSubclass(DummyModel):
    pass
