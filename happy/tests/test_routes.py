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
        d.add_route(controller1, '/')
        d.add_route(controller2, '/foo/:/bar/:')
        d.add_route(controller2, '/:/:')
        d.add_route(controller3, '/:/:foo/:bar/happy')

        from webob import Request
        req = Request.blank
        self.assertEqual(d(req('/')), 'One')
        self.assertEqual(d(req('/foo/cat/bar/dog')), ['Two', 'cat', 'dog'])
        self.assertEqual(d(req('/egg/bird')), ['Two', 'egg', 'bird'])
        self.assertEqual(d(req('/lily/barf/pi/happy')),
                         ['Three', 'lily', 'barf', 'pi'])
        self.assertEqual(d(req('/'), '/foo/bar/none'), None)