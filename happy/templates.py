import os
import webob

class Templates(object):
    """
    Helper class which retrieves templates out of a skin.  (See
    mod:``happy.skin``.)  The helper class is ignorant of any specific
    template implementations and relies on factory callables that are passed
    in to it in order to create templates.  A Templates object is created
    with a `skin` and a single default template factory.  Additional template
    factories can be registered for specific file extensions.  For template
    files that match the file registered file extension, the registered factory
    will be used instead of the default one.

    A template factory has the following signature::

        def factory(path_to_template_file):
            return template_callable

    The returned callable must have the following signature::

        def template_callable(**kw):
            return rendered_template_as_string

    Where `kw` is arbitrary arguments used to render the template.

    """
    Response = webob.Response # override point

    def __init__(self, skin, default_factory):
        self.skin = skin
        self.default_factory = default_factory
        self.factories = {}

    def register_factory(self, extension, factory):
        """
        Register a factory for a given file extension.
        """
        self.factories[extension] = factory

    def __getitem__(self, fname):
        """
        Allow dictionary like access to templates::

          templates = Templates(skin, factory)
          template = templates['templates/homepage.pt']

        """
        resource = self.skin.lookup(fname)
        if resource is None:
            raise KeyError(fname)
        extension = os.path.splitext(fname)[1].lstrip('.')
        factory = self.factories.get(extension, self.default_factory)
        return factory(resource.abspath())

    def render(self, fname, **kw):
        """
        Render template to a string and return the string.
        """
        return self[fname](**kw)

    def render_to_response(self, fname, **kw):
        """
        Renders template to a response object.  Content-type is set to
        'text/html'.  If template rendering returns a `unicode` object,
        response will be encoded as UTF-8.  If template returns a `str` object,
        however, no attempt will be made to guess the encoding.  Using
        templates that return `unicode` objects is recommended.
        """
        response = self.Response()
        response.content_type = 'text/html'

        body = self.render(fname, **kw)
        if isinstance(body, unicode):
            body = body.encode('UTF-8')
            response.charset = 'UTF-8'
        else:
            response.charset = None
        response.body = body

        return response

