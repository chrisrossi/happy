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

def _file_iter(path, buffer_size):
    f = open(path, 'rb')
    try:
        buf = f.read(buffer_size)
        while buf:
            yield buf
            buf = f.read(buffer_size)
    finally:
        f.close()
