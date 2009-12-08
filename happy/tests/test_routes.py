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
        d.register(controller1, '/')
        d.register(controller2, '/foo/:a/bar/:b')
        d.register(controller2, '/:a/:b')
        d.register(controller3, '/:a/:foo/:bar/happy')

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

        from happy.routes import RoutesDispatcher
        d = RoutesDispatcher()
        d.register(controller1, '/foo/:a/*')
        d.register(controller2, '/foo/bar/*')

        from webob import Request
        req = Request.blank
        self.assertEqual(d(req('/foo/man/choo')),
                         ('One', {'a': 'man'}, ['choo',]))
        self.assertEqual(d(req('/foo/bar/')),
                         ('Two', {}, []))
        self.assertEqual(d(req('/foo/bar/chew/toy')),
                         ('Two', {}, ['chew', 'toy']))

    def test_bad_wildcard(self):
        controller = lambda request: 'foo'
        from happy.routes import RoutesDispatcher
        d = RoutesDispatcher()
        self.assertRaises(ValueError, d.register, controller, '/foo/*/bar')

    def test_request_rewrite(self):
        controller = lambda request: (request.script_name, request.path_info)

        from happy.routes import RoutesDispatcher
        d = RoutesDispatcher()
        d.register(controller, '/foo/:a/*')

        from webob import Request
        req = Request.blank
        self.assertEqual(d(req('/foo/man/choo/man')),
                         ('/foo/man', '/choo/man'))
