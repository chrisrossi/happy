import webob

def wsgi_app(app, Request=webob.Request):
    """
    Transforms a happy responder into a WSGI application.  ``app`` is callable
    with signature: `app(request)` which returns a WebOb response or `None`.
    Responses of `None` will be replaced with a `404 Not Found` response.
    """
    def wrapper(environ, start_response):
        response = app(Request(environ))
        if response is None:
            response = webob.exc.HTTPNotFound()
        return response(environ, start_response)
    return wrapper
