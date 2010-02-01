import unittest

class TestViewRegistry(unittest.TestCase):
    def test_by_type(self):
        from happy.view import ViewRegistry
        from webob import Request
        request = Request.blank('/')
        registry = ViewRegistry()
        registry.register('view_a', Dummy)
        self.assertEqual(registry.lookup(request, Dummy()), 'view_a')
        self.assertEqual(registry.lookup(request, object()), None)

    def test_by_name(self):
        from happy.view import ViewRegistry
        from webob import Request
        request = Request.blank('/')
        registry = ViewRegistry()
        registry.register('foo_view', name='foo')
        self.assertEqual(registry.lookup(request, None, 'foo'), 'foo_view')

    def test_by_type_and_name(self):
        from happy.view import ViewRegistry
        from webob import Request
        request = Request.blank('/')
        registry = ViewRegistry()
        registry.register('view_a', Dummy)
        registry.register('foo_view', Dummy, 'foo')
        self.assertEqual(registry.lookup(request, Dummy()), 'view_a')
        self.assertEqual(registry.lookup(request, Dummy(), 'foo'), 'foo_view')

    def test_by_request_method(self):
        from happy.view import ViewRegistry
        from webob import Request
        request = Request.blank('/')
        registry = ViewRegistry()
        registry.register('get_view', Dummy, request_method='GET')
        registry.register('post_view', Dummy, request_method='POST')
        self.assertEqual(registry.lookup(request, Dummy()), 'get_view')
        request.method = 'POST'
        self.assertEqual(registry.lookup(request, Dummy()), 'post_view')

    def test_by_xhr(self):
        from happy.view import ViewRegistry
        from webob import Request
        request = Request.blank('/')
        registry = ViewRegistry()
        registry.register('true_view', Dummy, xhr=True)
        registry.register('false_view', Dummy)
        self.assertEqual(registry.lookup(request, Dummy()), 'false_view')
        request.headers['X-Requested-With'] = 'XMLHttpRequest'
        self.assertEqual(registry.lookup(request, Dummy()), 'true_view')

    def test_by_param_present(self):
        from happy.view import ViewRegistry
        from webob import Request
        request = Request.blank('/', POST={})
        registry = ViewRegistry()
        registry.register('show_view', Dummy)
        registry.register('submit_view', Dummy, request_param='submit')
        self.assertEqual(registry.lookup(request, Dummy()), 'show_view')
        request.POST['submit'] = 'submit'
        self.assertEqual(registry.lookup(request, Dummy()), 'submit_view')

    def test_by_param_value(self):
        from happy.view import ViewRegistry
        from webob import Request
        request = Request.blank('/', POST={})
        registry = ViewRegistry()
        registry.register('show_view', Dummy)
        registry.register('alt_view', Dummy, request_param='version=alt')
        self.assertEqual(registry.lookup(request, Dummy()), 'show_view')
        request.POST['version'] = 'normal'
        self.assertEqual(registry.lookup(request, Dummy()), 'show_view')
        request.POST['version'] = 'alt'
        self.assertEqual(registry.lookup(request, Dummy()), 'alt_view')

    def test_unknown_predicate(self):
        from happy.view import ViewRegistry
        from webob import Request
        request = Request.blank('/', POST={})
        registry = ViewRegistry()
        self.assertRaises(ValueError, registry.register, 'view', foo='foo')

class Dummy(object):
    pass
