from datetime import datetime
import mimetypes
import os
import webob

DEFAULT_BUFFER_SIZE = 1<<16 # 64 kilobytes
ISO_1123 = "%a, %d %b %Y %H:%M:%S GMT"

class FileResponse(webob.Response):
    """
    Serves a file from the filesystem.
    """
    def __init__(self, path, request=None,
                 buffer_size=DEFAULT_BUFFER_SIZE,
                 expires_timedelta=None):
        super(FileResponse, self).__init__()
        if request is None:
            request = webob.Request.blank('/')
        self.request = request

        self.last_modified = datetime.utcfromtimestamp(os.path.getmtime(path))

        # Check 'If-Modified-Since' request header
        # Browser might already have in cache
        modified_since = request.if_modified_since
        if modified_since is not None:
            if self.last_modified <= modified_since:
                self.status = 304
                return

        self.date = datetime.utcnow()
        self.app_iter = _file_iter(path, buffer_size)
        self.content_type = mimetypes.guess_type(path, strict=False)[0]
        self.content_length = os.path.getsize(path)
        if expires_timedelta is not None:
            self.expires = self.date + expires_timedelta
        else:
            self.expires = self.date

class DirectoryApplication(object):
    """
    Serves files out of a directory on the filesystem.
    """
    FileResponse = FileResponse # override point

    def __init__(self, docroot,
                 buffer_size=DEFAULT_BUFFER_SIZE,
                 expires_timedelta=None):
        self.docroot = docroot
        self.buffer_size = buffer_size
        self.expires_timedelta = expires_timedelta

    def __call__(self, request):
        filepath = os.path.join(self.docroot, request.path_info.strip('/'))
        if os.path.isdir(filepath):
            return self.index_directory(request)

        elif os.path.isfile(filepath):
            path, fname = os.path.split(filepath)
            if fname[0] not in ('.', '_'):  # Hide hidden files
                return self.FileResponse(
                    filepath, request,
                    buffer_size=self.buffer_size,
                    expires_timedelta=self.expires_timedelta
                )

    def index_directory(self, request):
        """
        Override this method to provide a directory index view, if you're into
        that kind of thing.
        """

def _file_iter(path, buffer_size):
    f = open(path, 'rb')
    try:
        buf = f.read(buffer_size)
        while buf:
            yield buf
            buf = f.read(buffer_size)
    finally:
        f.close()
