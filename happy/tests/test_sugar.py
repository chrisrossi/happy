import unittest

class WsgiAppTests(unittest.TestCase):
    def test_response(self):
        def dummy_app(request):
            def dummy_response(environ, start_response):
                return "DUMMY"
            return dummy_response

        from happy.sugar import wsgi_app
        fut = wsgi_app(dummy_app)

        environ = {}
        start_response = object()
        self.assertEqual(fut(environ, start_response), 'DUMMY')

    def test_no_response(self):
        def dummy_app(request):
            return None

        from happy.sugar import wsgi_app
        fut = wsgi_app(dummy_app)

        environ = {}
        start_response = object()
        self.assertEqual(fut(environ, start_response).status_int, 404)
