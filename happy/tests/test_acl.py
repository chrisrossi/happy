import unittest

class TestMay(unittest.TestCase):
    def test_no_acl(self):
        from happy.acl import may
        context = DummyModel()
        self.failIf(may(['chris', 'group.Admin'], 'view', context))

    def test_local_acl_allow(self):
        from happy.acl import may
        from happy.acl import Allow
        context = DummyModel()
        context.__acl__ = [
            (Allow, 'chris', ['view']),
        ]
        self.failUnless(may(['chris', 'group.Admin'], 'view', context))

    def test_local_acl_deny(self):
        from happy.acl import may
        from happy.acl import Allow
        from happy.acl import Deny
        context = DummyModel()
        context.__acl__ = [
            (Deny, 'chris', ['havefun']),
            (Allow, 'group.Admin', ['havefun']),
        ]
        self.failIf(may(['chris', 'group.Admin'], 'havefun', context))

    def test_inherit_acl(self):
        from happy.acl import may
        from happy.acl import Allow
        from happy.acl import ALL_PERMISSIONS
        from happy.acl import Deny
        root = DummyModel()
        context = root['foo'] = DummyModel()
        root.__acl__ = [
            (Allow, 'Everyone', 'view'),
            (Allow, 'group.Admin', 'view,edit'),
            (Deny, 'Everyone', ALL_PERMISSIONS),
        ]
        self.failUnless(may(['chris', 'Everyone'], 'view', context))
        self.failUnless(may(['chris', 'group.Admin'], 'edit', context))
        self.failIf(may(['chris', 'Everyone'], 'edit', context))

class TestRequirePermission(unittest.TestCase):
    def test_basic_deny_allow(self):
        from happy.acl import require_permission
        @require_permission('view')
        def app(request):
            return 'OK'

        import webob
        from happy.acl import Allow
        request = webob.Request.blank('/')
        request.context = DummyModel()
        request.remote_user = 'chris'
        request.authenticated_principals = ['chris']
        self.assertEqual(app(request).status_int, 403)

        request.context.__acl__ = [
            (Allow, 'chris', ['view']),
        ]
        self.assertEqual(app(request), 'OK')

    def test_not_logged_in(self):
        from happy.acl import require_permission
        @require_permission('view')
        def app(request):
            return 'OK' #pragma NO COVERAGE, shouldn't be called

        import webob
        from happy.acl import Allow
        request = webob.Request.blank('/')
        request.context = DummyModel()
        self.assertEqual(app(request).status_int, 401)

class DummyModel(dict):
    def __setitem__(self, name, child):
        super(DummyModel, self).__setitem__(name, child)
        child.__name__ = name
        child.__parent__ = self
