"""
Tools for providing user authentication.  There are a handful of component
interfaces that are used::

    interface IPasswordBroker:
        # An IPasswordBroker interface is responsible for checking passwords
        # of user logins.

        def __call__(login, password):
            # Return boolean indicating whether password is valid for
            # given login.

    interface IPrincipalsBroker:
        # An IPrincipalsBroker is responsible for retrieving the principals for
        # a given login.  Principals are arbitrary strings that identify a user
        # and/or any roles that user has or groups he is a part of.  The actual
        # meaning of any given principal is application specific.  Note that we
        # make a distinction between userid and login.  A login is an
        # identifier typed in by a user to identify herself when logging in.  A
        # userid is used internally by an application to identify a user.
        # While the login and userid could certainly be the same identifier,
        # the login is considered to be mutable whereas the userid is generally
        # considered be eternally immutable. The distinction helps when a user
        # wants to change their login for some reason.  If there is a notion of
        # resource ownership or an audit trail, etc, that refererences users by
        # ids, these datastructures can be left alone when updating the login.

        def get_userid(login):
            # Returns userid for given login

        def get_principals(login):
            # Returns principals for given login.  `userid` will always be
            # first principal.  Principals are arbitrary, application
            # specific strings that usually describe things like group
            # membership, etc...

    interface ICredentialBroker:
        # In the context of `happy.login` a credential is an arbitrary
        # string, usually cryptographically strong, that acts like a key
        # to identify a logged in user.  A credential is appropriate to hand
        # to a browser as a cookie upon successful login.  An ICredentialBroker
        # instance is responsible for generating credentials, and retrieving
        # a user's login from a credential.  Optionally, the ICredentialBroker,
        # can log a user out by invalidating a particular credential.  This
        # last function is optional since some implementations might rely on
        # storing a user's login cryptographically inside the credential itself
        # (for example, in an AuthTicket system) rather than maintaining a
        # persistent mapping of credential to login.

        def login(login):
            # Generates a new credential for a particular login, ie, logs in a
            # user.

        def get_login(credential):
            # Retrieves a user's login for a given credential.  May return
            # `None` if the credential is invalid or the user has been logged
            # out.  Effectively checks whether a user is logged in.

        def logout(credential):
            # Invalidate a given credential.  Applications can check to see if
            # this operation is supported by checking for the `logout`
            # attribute on a given instance::
            #
            #   logout_supported = hasattr(credential_broker, 'logout')
            #
            # Implementations that do not support logout should not define this
            # method.

"""
from __future__ import with_statement

import anydbm
import crypt
import uuid
import webob

from webob.exc import HTTPFound

class FormLoginMiddleware(object):
    """
    Handles login via a form and cookies.
    """
    Request = webob.Request # Override point

    def __init__(self, app, password_broker, principals_broker,
                 credential_broker, form_template=None, login_path='/login',
                 logout_path='/logout', cookie_name='happy.login',
                 redirect_401=True, redirect_403=False):
        self.app = app
        self.password_broker = password_broker
        self.principals_broker = principals_broker
        self.credential_broker = credential_broker
        if form_template is None:
            self.form_template = self._default_template
        else:
            self.form_template = form_template
        self.login_path = login_path
        self.logout_path = logout_path
        self.cookie_name = cookie_name
        self.redirect_401 = redirect_401
        self.redirect_403 = redirect_403

    def __call__(self, request):
        if request.path_info == self.login_path:
            return self._login(request)

        credential = request.cookies.get(self.cookie_name, None)
        if request.path_info == self.logout_path:
            return self._logout(request, credential)

        if credential is not None:
            login = self.credential_broker.get_login(credential)
            if login is not None:
                request = self.Request(request.environ.copy())
                request.remote_user = self.principals_broker.get_userid(login)
                request.authenticated_principals = \
                       self.principals_broker.get_principals(login)

        response = self.app(request)
        if response is not None:
            if response.status_int == 401:
                if self.redirect_401:
                    return HTTPFound(location=self._login_url(request))
            elif response.status_int == 403:
                if self.redirect_403:
                    return HTTPFound(location=self._login_url(request))

        return response

    def _login_url(self, request):
        return request.application_url.rstrip('/') + self.login_path

    def _login(self, request):
        login = request.params.get('login', '')
        password = request.params.get('password', None)
        status_msg = request.params.get('status_msg', '')
        redirect_to = request.params.get('redirect_to', None)
        if redirect_to is None:
            redirect_to = request.application_url
        if login and password:
            if self.password_broker(login, password):
                credential = self.credential_broker.login(login)
                response = HTTPFound(location=redirect_to)
                response.set_cookie(self.cookie_name, credential)
                return response

            status_msg = "Bad login"

        body = self.form_template(
            login=login,
            status_msg=status_msg,
            redirect_to=redirect_to,
        )
        return webob.Response(body, content_type='text/html')

    def _logout(self, request, credential):
        if hasattr(self.credential_broker, 'logout'):
            self.credential_broker.logout(credential)

        redirect_to = request.params.get('redirect_to', None)
        if redirect_to is None:
            redirect_to = request.application_url
        response = HTTPFound(location=redirect_to)
        response.delete_cookie(self.cookie_name)
        return response

    def _default_template(self, **kw):
        """
        Developers are highly encouraged to provide their own template.  No
        attempt will ever be made to make this default not suck.
        """
        return u"""
            <html>
              <head>
                <title>Log In</title>
                <style>
                  form {
                    padding: 1em;
                    border: 1px solid black;
                  }

                  .status {
                    color: red;
                  }
                </style>
              </head>
              <body>
                <form method="POST" name="login">
                  <input type="hidden" name="redirect_to"
                         value="%(redirect_to)s"/>
                  <input name="login" value="%(login)s"/>
                  <b>login</b><br/>
                  <input name="password" type="password"/>
                  <b>password</b><br/>
                  <br/>
                  <input type="submit" value="login"/><br/>
                  <div class="status">%(status_msg)s</div>
                </form>
              </body>
            </html>
        """ % kw


class HtpasswdBroker(object):
    """
    Performs authentication against users and passwords stored in a standard
    format htpasswd file.  The file is of the same format produced by Apache's
    ``htpasswd`` program which cames standard with the Apache web server.
    Files in this format are also easily produced by simple Python scripts.
    See: http://pacopablo.com/wiki/pacopablo/blog/htpasswd-with-python
    """
    def __init__(self, htpasswd_file):
        passwords = {}
        with open(htpasswd_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                login, encrypted = line.split(':')
                passwords[login] = encrypted

        self.passwords = passwords

    def __call__(self, login, password):
        if not login in self.passwords:
            return False
        encrypted = self.passwords[login]
        return crypt.crypt(password, encrypted) == encrypted

class FlatFilePrincipalsBroker(object):
    """
    Reference implementation of IPrincipalsBroker that just reads principals
    stored in a flat file.  File is of format:

      login1: principal1, principal2, etc...
      login2: etc...
    """
    def __init__(self, db_file):
        mapping = {}
        with open(db_file) as f:
            for line in f:
                if line.startswith('#'):
                    continue
                line = unicode(line.strip(), 'utf-8')
                if not line:
                    continue
                login, principals = map(lambda x: x.strip(), line.split(':'))
                principals = map(lambda x: x.strip(), principals.split(','))
                mapping[login] = [p for p in principals if p]

        self._principals = mapping

    def get_principals(self, login):
        return self._principals[login]

    def get_userid(self, login):
        return self.get_principals(login)[0]


class RandomUUIDCredentialBroker(object):
    """
    Reference implementation of ICredentialBroker.  Maintains a simple dict
    of credential to login mappings.  If a filename is provided to the
    constructor, the mapping will be persisted to the file using the `anydbm`
    module from the Python standard library.
    """
    def __init__(self, db_file=None):
        if db_file is not None:
            self._db = anydbm.open(db_file, 'c')
        else:
            self._db = {}

    def login(self, login):
        credential = str(uuid.uuid4())
        self._db[credential] = login
        return credential

    def get_login(self, credential):
        return self._db.get(credential, None)

    def logout(self, credential):
        if credential in self._db:
            del self._db[credential]
