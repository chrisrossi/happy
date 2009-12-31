import unittest

class RoutesTests(unittest.TestCase):
    def test_dispatch(self):
        def controller1(request):
            return 'One'
        def controller2(request, a, b):
            return ['Two', a, b]
        def controller3(request, a, bar, foo):
            return ['Three', a, foo, bar]

        from happy.routes import RoutesDispatcher
        d = RoutesDispatcher()
        d.register(controller1, 'root', '/')
        d.register(controller2, 'one', '/foo/:a/bar/:b')
        d.register(controller2, 'two', '/:a/:b')
        d.register(controller3, 'three', '/:a/:foo/:bar/happy')

        from webob import Request
        req = Request.blank
        self.assertEqual(d(req('/')), 'One')
        self.assertEqual(d(req('/foo/cat/bar/dog')), ['Two', 'cat', 'dog'])
        self.assertEqual(d(req('/egg/bird')), ['Two', 'egg', 'bird'])
        self.assertEqual(d(req('/lily/barf/pi/happy')),
                         ['Three', 'lily', 'barf', 'pi'])
        self.assertEqual(d(req('/'), '/foo/bar/none'), None)

    def test_wildcard(self):
        def controller1(request):
            return 'One', request.match_dict, request.subpath

        def controller2(request):
            return 'Two', request.match_dict, request.subpath

        def controller3(request):
            return 'Three', request.match_dict, request.subpath

        from happy.routes import RoutesDispatcher
        d = RoutesDispatcher()
        d.register(controller1, 'foo', '/foo/:a/*')
        d.register(controller2, 'foobar_plus', '/foo/bar/*')

        from webob import Request
        req = Request.blank
        self.assertEqual(d(req('/foo/man/choo')),
                         ('One', {'a': 'man'}, ['choo',]))
        self.assertEqual(d(req('/foo/bar/')),
                         ('Two', {}, []))
        self.assertEqual(d(req('/foo/bar/chew/toy')),
                         ('Two', {}, ['chew', 'toy']))

        d.register(controller3, 'foobar', '/foo/bar/')
        self.assertEqual(d(req('/foo/bar/chew/toy')),
                         ('Two', {}, ['chew', 'toy']))
        self.assertEqual(d(req('/foo/bar/')),
                         ('Three', {}, []))

    def test_bad_wildcard(self):
        controller = lambda request: 'foo'
        from happy.routes import RoutesDispatcher
        d = RoutesDispatcher()
        self.assertRaises(ValueError, d.register, controller, '', '/foo/*/bar')

    def test_request_rewrite(self):
        controller = lambda request: (request.script_name, request.path_info)

        from happy.routes import RoutesDispatcher
        d = RoutesDispatcher()
        d.register(controller, 'a', '/foo/:a/*')

        from webob import Request
        req = Request.blank
        self.assertEqual(d(req('/foo/man/')),
                         ('/foo/man/', ''))
        self.assertEqual(d(req('/foo/man/choo/man')),
                         ('/foo/man', '/choo/man'))
        self.assertEqual(d(req('/foo/man/choo/man/')),
                         ('/foo/man', '/choo/man/'))

    def test_instance_callable(self):
        class Controller(object):
            def __call__(self, request):
                return 'Hello'

        from happy.routes import RoutesDispatcher
        d = RoutesDispatcher()
        d.register(Controller(), 'root', '/')

        from webob import Request
        self.assertEqual(d(Request.blank('/')), 'Hello')

    def test_preserve_trailing_slash(self):
        controller1 = lambda request: (1, request.url)
        controller2 = lambda request: (2, request.url)

        from happy.routes import RoutesDispatcher
        d = RoutesDispatcher()
        d.register(controller1, 'foobar', '/foo/bar/')
        d.register(controller2, 'fooplus', '/foo/*')

        from webob import Request
        req = Request.blank
        self.assertEqual(d(req('/foo/bar/')), (1, 'http://localhost/foo/bar/'))
        self.assertEqual(d(req('/foo/cat/')), (2, 'http://localhost/foo/cat/'))

    def test_get_route_by_name(self):
        controller = lambda x: x

        from happy.routes import RoutesDispatcher
        d = RoutesDispatcher()
        d.register(controller, 'foo', '/foo/*')
        self.assertEquals(d['foo'].path, '/foo/*')

    def test_url(self):
        controller = lambda x: x

        from happy.routes import RoutesDispatcher
        d = RoutesDispatcher()
        d.register(controller, 'one', '/foo/bar/*')
        d.register(controller, 'two', '/foo/:bar')
        d.register(controller, 'three', '/foo/:bar/')

        import webob
        request = webob.Request.blank('/')
        one = d['one']
        two = d['two']
        three = d['three']

        self.assertEqual(one.url(request), 'http://localhost/foo/bar/')
        self.assertEqual(one.url(request, {}, ['bean', 'cheese']),
                         'http://localhost/foo/bar/bean/cheese')
        self.assertEqual(two.url(request, {'bar': 'booze'}),
                         'http://localhost/foo/booze')
        self.assertEqual(three.url(request, {'bar': 'booze'}),
                         'http://localhost/foo/booze/')
