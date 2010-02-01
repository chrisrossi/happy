import unittest

class TraversalTests(unittest.TestCase):
    def test_traverse(self):
        from happy.traversal import traverse as f
        root = DummyModel()
        a = root['a'] = DummyModel()
        b = root['b'] = DummyModel()
        c = b['c'] = DummyModel()
        d = a['d'] = DummyLeaf()
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

    def test_find_model(self):
        from happy.traversal import find_model as f
        root = DummyModel()
        a = root['a'] = DummyModel()
        b = root['b'] = DummyModel()
        c = b['c'] = DummyModel()
        d = a['d'] = DummyLeaf()
        e = root['e'] = DummyModel()
        g = e['g'] = DummyModel()
        h = e['h'] = DummyModel()

        self.assertEqual(f(root, ''), root)
        self.assertEqual(f(root, '/'), root)
        self.assertEqual(f(root, '/a'), a)
        self.assertEqual(f(root, '/a/'), a)
        self.assertRaises(KeyError, f, root, '/a/d/f')
        self.assertEqual(f(root, '/b/c'), c)
        self.assertRaises(KeyError, f, root, '/b/c/d/e')

class TraversalDispatcherTests(unittest.TestCase):
    def test_default_view(self):
        root = DummyModel()
        root_factory = lambda request: root
        from happy.traversal import TraversalDispatcher
        dispatcher = TraversalDispatcher(root_factory)
        calls = []
        def view(request, context):
            calls.append((request, context))
        dispatcher.register(view, DummyModel)
        from webob import Request
        request = Request.blank('/')
        dispatcher(request)
        self.assertEqual(calls[0], (request, root))

    def test_named_view(self):
        root = DummyModel()
        root_factory = lambda request: root
        from happy.traversal import TraversalDispatcher
        dispatcher = TraversalDispatcher(root_factory)
        def view(request, context):
            return 'Hello'

        dispatcher.register(view, DummyModel, 'hello')
        from webob import Request
        response = dispatcher(Request.blank('/'))
        self.assertEqual(response, None)
        response = dispatcher(Request.blank('/hello'))
        self.assertEqual(response, 'Hello')

class TestModelURL(unittest.TestCase):
    def test_it(self):
        root = DummyModel()
        b = root['b'] = DummyModel()
        c = b['c'] = DummyModel()

        import webob
        req = webob.Request.blank('/')

        from happy.traversal import model_url
        self.assertEqual(model_url(req, root), 'http://localhost/')
        self.assertEqual(model_url(req, c), 'http://localhost/b/c/')
        self.assertEqual(model_url(req, c, 'foo', 'bar'),
                         'http://localhost/b/c/foo/bar')

class DummyModel(dict):
    def __setitem__(self, name, value):
        super(DummyModel, self).__setitem__(name, value)
        value.__name__ = name
        value.__parent__ = self

    def __eq__(self, other):
        return self is other

class DummyLeaf(object):
    pass

class DummyModelSubclass(DummyModel):
    pass
