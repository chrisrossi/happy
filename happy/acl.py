"""
Implements acl based security.  Largely ripped off from repoze.bfg.
"""
from webob.exc import HTTPForbidden
from webob.exc import HTTPUnauthorized

Everyone = 'system.Everyone'
Authenticated = 'system.Authenticated'
Allow = 'Allow'
Deny = 'Deny'

class AllPermissionsList(object):
    """ Stand in 'permission list' to represent all permissions """
    #def __iter__(self):
    #    return ()
    def __contains__(self, other):
        return True
    #def __eq__(self, other):
    #    return isinstance(other, self.__class__)

ALL_PERMISSIONS = AllPermissionsList()
DENY_ALL = (Deny, Everyone, ALL_PERMISSIONS)

def may(principals, permission, context):
    """
    Returns boolean indicating whether user with given principals has given
    permission on the given context.
    """
    for node in _lineage(context):
        acl = getattr(node, '__acl__', None)
        if acl is None:
            continue

        for access, principal, permissions in acl:
            if principal in principals and permission in permissions:
                return access == Allow

def require_permission(permission):
    """
    Decorate a responder callable to require a particular permission.
    """
    def decorator(app):
        def wrapper(request):
            context = getattr(request, 'context', None)
            principals = getattr(request, 'authenticated_principals', [])
            effective_principals = [Everyone] + principals
            if request.remote_user:
                effective_principals.append(Authenticated)
            if may(effective_principals, permission, context):
                return app(request)
            elif request.remote_user:
                return HTTPForbidden()
            return HTTPUnauthorized()
        return wrapper
    return decorator

def _lineage(context):
    yield context
    parent = getattr(context, '__parent__', None)
    if parent is not None:
        for ancestor in _lineage(parent):
            yield ancestor
