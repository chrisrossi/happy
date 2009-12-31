import os
import pkg_resources

class Skin(object):
    """
    Allows retrieval of resources that are organized into skin layers.  Each
    skin layer is either a directory in the filesystem or a package spec::

      skin = Skin(
          '/path/to/user/customizations',
          'mypackage.views:skin',
      )

    When searching for a resource, skins are consulted in order until a
    matching resource is found.
    """
    def __init__(self, *layers):
        self._layers = [_make_layer(layer) for layer in layers]

    def add_layer(self, layer):
        """
        Adds a layer to the search path.  This layer will be consulted before
        any previously registered layers.
        """
        self._layers.insert(0, _make_layer(layer))

    def lookup(self, fname):
        """
        Looks up a resource using registered skin layers.  Returns a resource
        object or `None`.  Resource may have different implementations but
        share a common interface::

            interface IResource:
                def stream():
                    Returns file-like object that can be read to retrieve the
                    contents of the resource.  The resource is read in binary
                    mode.

                def string():
                    Reads the entire resource into memory and returns the
                    contents in a binary string.

                def abspath():
                    Returns the absolute path to the resource in the
                    filesystem.  If the resource is inside a zipped egg or
                    otherwise wouldn't be accessible as a file, it is extracted
                    to a temporary file on the filesystem.  (This behavior is
                    actually implemented in `pkg_resources` which is part of
                    `setuptools`.)

                def isdir():
                    Returns `True` if resource is a directory, otherwise
                    returns `False`.

                def listdir():
                    Works just like `os.listdir`.
        """
        for layer in self._layers:
            resource = layer.lookup(fname)
            if resource is not None:
                return resource

def _make_layer(spec):
    if os.path.isdir(spec):
        return _FolderLayer(os.path.abspath(spec))

    # XXX Check to make sure package exists?
    return _PackageLayer(spec)

class _FolderLayer(object):
    def __init__(self, path):
        self.path = path

    def lookup(self, fname):
        fpath = os.path.join(self.path, fname)
        if os.path.exists(fpath):
            return _FileSystemResource(fpath)

class _FileSystemResource(object):
    def __init__(self, path):
        self.path = path

    def stream(self):
        return open(self.path, 'rb')

    def string(self):
        return self.stream().read()

    def abspath(self):
        return self.path

    def isdir(self):
        return os.path.isdir(self.path)

    def listdir(self):
        return os.listdir(self.path)

class _PackageLayer(object):
    def __init__(self, spec):
        if ':' in spec:
            self.pkg_name, self.path = spec.split(':')
        else:
            self.pkg_name, self.path = spec, ''

    def lookup(self, fname):
        fpath = os.path.join(self.path, fname)
        if pkg_resources.resource_exists(self.pkg_name, fpath):
            return _PackageResource(self.pkg_name, fpath)

class _PackageResource(object):
    def __init__(self, pkg_name, path):
        self.pkg_name = pkg_name
        self.path = path

    def stream(self):
        return pkg_resources.resource_stream(self.pkg_name, self.path)

    def string(self):
        return pkg_resources.resource_string(self.pkg_name, self.path)

    def abspath(self):
        return pkg_resources.resource_filename(self.pkg_name, self.path)

    def isdir(self):
        return pkg_resources.resource_isdir(self.pkg_name, self.path)

    def listdir(self):
        return pkg_resources.resource_listdir(self.pkg_name, self.path)

from happy.static import DEFAULT_BUFFER_SIZE
from happy.static import FileResponse

class SkinApplication(object):
    """
    Application that serves static resources from inside a skin.
    """
    FileResponse = FileResponse # override point

    def __init__(self, skin,
                 buffer_size=DEFAULT_BUFFER_SIZE,
                 expires_timedelta=None):
        self.skin = skin
        self.buffer_size = buffer_size
        self.expires_timedelta = expires_timedelta

    def __call__(self, request):
        resource = self.skin.lookup(request.path_info.strip('/'))
        if resource is not None:
            if resource.isdir():
                return self.index_directory(request, resource)

            return self.FileResponse(
                    resource.abspath(), request,
                    buffer_size=self.buffer_size,
                    expires_timedelta=self.expires_timedelta
                )

    def index_directory(self, request, resource):
        """
        Override this method to provide a directory index view, if you're into
        that kind of thing.
        """

