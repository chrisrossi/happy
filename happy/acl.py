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

def effective_principals(request):
    principals = getattr(request, 'authenticated_principals', [])
    effective_principals = [Everyone] + principals
    if request.remote_user:
        effective_principals.append(Authenticated)
    return effective_principals

def has_permission(request, permission, context=None):
    if context is None:
        context = getattr(request, 'context', None)
    return may(effective_principals(request), permission, context)

def principals_with_permission(permission, context):
    # Stolen direct from bfg, comments and all
    allowed = set()

    for location in reversed(list(_lineage(context))):
        # NB: we're walking *up* the object graph from the root
        acl = getattr(location, '__acl__', None)
        if acl is None:
            continue

        allowed_here = set()
        denied_here = set()

        for ace_action, ace_principal, ace_permissions in acl:
            if ace_action == Allow and permission in ace_permissions:
                if not ace_principal in denied_here:
                    allowed_here.add(ace_principal)
            if ace_action == Deny and permission in ace_permissions:
                denied_here.add(ace_principal)
                if ace_principal == Everyone:
                    # clear the entire allowed set, as we've hit a
                    # deny of Everyone ala (Deny, Everyone, ALL)
                    allowed = set()
                    break
                elif ace_principal in allowed:
                    allowed.remove(ace_principal)

        allowed.update(allowed_here)

    return allowed

def require_permission(permission):
    """
    Decorate a responder callable to require a particular permission.
    """
    def decorator(app):
        def wrapper(request, *args, **kw):
            if has_permission(request, permission):
                return app(request, *args, **kw)
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
