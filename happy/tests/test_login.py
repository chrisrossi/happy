import unittest

class TestFormLoginMiddleware(unittest.TestCase):
    def _make_one(self, app, **kw):
        from happy.login import FormLoginMiddleware
        return FormLoginMiddleware(
            app,
            DummyPasswordBroker(),
            DummyPrincipalsBroker(),
            DummyCredentialBroker(),
            **kw
        )

    def test_login_logout(self):
        from webob import Request
        fut = self._make_one(dummy_app)

        request = Request.blank('/')
        response = fut(request)
        self.assertEqual(response.remote_user, None)
        self.assertEqual(response.principals, None)

        request = Request.blank('/login')
        response = fut(request)
        self.failUnless('login' in response.body)

        request = Request.blank('/login', POST={
            'login': 'chris@example.com',
            'password': '12345678'
            }
        )
        response = fut(request)
        credential = get_cookie(response, 'happy.login')
        self.failUnless(credential)
        self.assertEqual(response.location, 'http://localhost')

        request = Request.blank('/')
        request.cookies['happy.login'] = credential
        response = fut(request)
        self.assertEqual(response.remote_user, 'user-1234')
        self.assertEqual(response.principals,
                         ['user-1234', 'group.Administrators'])

        request = Request.blank('/logout')
        request.cookies['happy.login'] = credential
        response = fut(request)
        credential = get_cookie(response, 'happy.login')
        self.failIf(credential)
        self.assertEqual(response.location, 'http://localhost')

        request = Request.blank('/')
        request.cookies['happy.login'] = credential
        response = fut(request)
        self.assertEqual(response.remote_user, None)
        self.assertEqual(response.principals, None)

    def test_custom_form_template(self):
        def dummy_template(**kw):
            assert kw['login'] ==  'chris'
            assert kw['redirect_to'] == 'foo'
            assert kw['status_msg'] == 'message'
            return 'Howdy!'

        from webob import Request
        fut = self._make_one(dummy_app, form_template=dummy_template)
        request = Request.blank(
            '/login?status_msg=message&redirect_to=foo&login=chris'
        )
        self.assertEqual(fut(request).body, 'Howdy!')

    def test_login_bad_login(self):
        from webob import Request
        fut = self._make_one(dummy_app)
        request = Request.blank(
            '/login',
            POST=dict(login='chris', password='12345678')
        )
        body = fut(request).body
        self.failUnless('Bad login' in body, body)

    def test_login_bad_password(self):
        from webob import Request
        fut = self._make_one(dummy_app)
        request = Request.blank(
            '/login',
            POST=dict(login='chris@example.com', password='123456789')
        )
        body = fut(request).body
        self.failUnless('Bad login' in body, body)

    def test_redirect_401(self):
        def app(request):
            return DummyResponse(401)

        from webob import Request
        fut = self._make_one(app)
        request = Request.blank('/')
        self.assertEqual(fut(request).location, 'http://localhost/login')

    def test_dont_redirect_401(self):
        def app(request):
            return DummyResponse(401)

        from webob import Request
        fut = self._make_one(app, redirect_401=False)
        request = Request.blank('/')
        self.assertEqual(fut(request).status_int, 401)

    def test_redirect_403(self):
        def app(request):
            return DummyResponse(403)

        from webob import Request
        fut = self._make_one(app, redirect_403=True)
        request = Request.blank('/')
        self.assertEqual(fut(request).location, 'http://localhost/login')

    def test_dont_redirect_403(self):
        def app(request):
            return DummyResponse(403)

        from webob import Request
        fut = self._make_one(app)
        request = Request.blank('/')
        self.assertEqual(fut(request).status_int, 403)


class TestHtpasswdAuthenticator(unittest.TestCase):
    def setUp(self):
        import os
        import tempfile
        fd, self.htpasswd_file = tempfile.mkstemp('.lever.auth.test')
        os.close(fd)

        with open(self.htpasswd_file, 'w') as f:
            print >>f, "# temp file for testing"

    def tearDown(self):
        import os
        os.remove(self.htpasswd_file)

    def _make_one(self):
        from happy.login import HtpasswdBroker
        return HtpasswdBroker(self.htpasswd_file)

    def _add_user_password(self, login, passwd):
        import crypt
        with open(self.htpasswd_file, 'a') as f:
            print >>f, '%s:%s' % (login, crypt.crypt(passwd, 'salt'))

    def test_good_passwd(self):
        self._add_user_password('chris', 'rossi')
        authenticator = self._make_one()
        self.failUnless(authenticator('chris', 'rossi'))

    def test_bad_passwd(self):
        self._add_user_password('chris', 'rossi')
        authenticator = self._make_one()
        self.failIf(authenticator('chris', 'schmidt'))

    def test_bad_user(self):
        self._add_user_password('chris', 'rossi')
        authenticator = self._make_one()
        self.failIf(authenticator('mike', 'schmidt'))


class TestFlatFilePrincipalsBrokerTests(unittest.TestCase):
    def setUp(self):
        import os
        import tempfile
        self.fname = tempfile.mktemp('.lever.auth.test')

        with open(self.fname, 'w') as f:
            print >>f, "# temp file for testing"
            print >>f, ""

    def tearDown(self):
        import os
        os.remove(self.fname)

    def _make_one(self):
        from happy.login import FlatFilePrincipalsBroker
        return FlatFilePrincipalsBroker(self.fname)

    def _add_user_principals(self, login, principals):
        import crypt
        principals = ', '.join(principals).encode('utf-8')
        with open(self.fname, 'a') as f:
            print >>f, '%s: %s' % (login, principals)

    def test_has_principals(self):
        principals = [
            u'1234',
            u'soccer players',
            u'qualit\xe0',
        ]
        self._add_user_principals('fumanchu', principals)
        provider = self._make_one()
        self.assertEqual(provider.get_principals('fumanchu'), principals)
        self.assertEqual(provider.get_userid('fumanchu'), '1234')

class TestRandomUUIDCredentialBroker(unittest.TestCase):
    def test_in_memory(self):
        from happy.login import RandomUUIDCredentialBroker
        broker = RandomUUIDCredentialBroker()
        credential = broker.login('fumanchu')
        self.assertEqual(broker.get_login(credential), 'fumanchu')
        broker.logout(credential)
        self.assertEqual(broker.get_login(credential), None)

    def test_persistent(self):
        import os
        import tempfile
        tmpdir = tempfile.mkdtemp('_happy_test')
        db_file = os.path.join(tmpdir, 'credentials.db')

        from happy.login import RandomUUIDCredentialBroker
        broker = RandomUUIDCredentialBroker(db_file)
        credential = broker.login('fumanchu')
        self.assertEqual(broker.get_login(credential), 'fumanchu')

        broker = RandomUUIDCredentialBroker(db_file)
        self.assertEqual(broker.get_login(credential), 'fumanchu')

        broker.logout(credential)
        self.assertEqual(broker.get_login(credential), None)

        broker = RandomUUIDCredentialBroker(db_file)
        self.assertEqual(broker.get_login(credential), None)

class DummyPasswordBroker(object):
    _passwords = {
        'chris@example.com': '12345678',
    }

    def __call__(self, login, password):
        return login in self._passwords and self._passwords[login] == password

class DummyPrincipalsBroker(object):
    _principals = {
        'chris@example.com': ['user-1234', 'group.Administrators']
    }

    def get_userid(self, login):
        return self._principals[login][0]

    def get_principals(self, login):
        return self._principals[login]

class DummyCredentialBroker(object):
    def __init__(self):
        self._credentials = {}

    def login(self, login):
        import uuid
        credential = str(uuid.uuid4())
        self._credentials[credential] = login
        return credential

    def logout(self, credential):
        del self._credentials[credential]

    def get_login(self, credential):
        return self._credentials.get(credential, None)

class DummyResponse(object):
    def __init__(self, status_int=200):
        self.status_int = status_int

def dummy_app(request):
    response = DummyResponse()
    response.remote_user = request.remote_user
    response.principals = getattr(
        request, 'authenticated_principals', None
    )
    return response

def get_cookie(response, cookie_name):
    for k, v in response.headers.items():
        if k == 'Set-Cookie':
            name, value = v.split(';')[0].split('=')
            if name == cookie_name:
                return value