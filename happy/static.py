from datetime import datetime
import mimetypes
import os
import webob

DEFAULT_BUFFER_SIZE = 1<<16 # 64 kilobytes

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

        # Provide partial response if requested
        content_length = os.path.getsize(path)
        request_range = self._get_range(content_length)
        if request_range is not None:
            start, end = request_range
            if start >= content_length:
                self.status_int = 416 # Request range not satisfiable
                return

            self.status_int = 206 # Partial Content
            self.headers['Content-Range'] = 'bytes %d-%d/%d' % (
                start, end-1, content_length)

        self.date = datetime.utcnow()
        self.app_iter = _file_iter(path, buffer_size, request_range)
        self.content_type = mimetypes.guess_type(path, strict=False)[0]
        self.content_length = content_length
        if expires_timedelta is not None:
            self.expires = self.date + expires_timedelta
        else:
            self.expires = self.date

    def _get_range(self, content_length):
        # WebOb earlier than 0.9.7 has broken range parser implementation.
        # The current released version at this time is 0.9.6, so we do this
        # ourselves.  (It is fixed on trunk, though.)
        request = self.request
        range_header = request.headers.get('Range', None)
        if range_header is None:
            return None

        # Refuse to parse multiple byte ranges.  They are just plain silly.
        if ',' in range_header:
            return None

        unit, range_s = range_header.split('=', 1)
        if unit != 'bytes':
            # Other units are not supported
            return None

        if range_s.startswith('-'):
            start = content_length - int(range_s[1:])
            return start, content_length

        start, end = map(int, range_s.split('-'))
        return start, end + 1

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

def _file_iter(path, buffer_size, content_range=None):
    f = open(path, 'rb')
    if content_range is not None:

        class ByteReader():
            def __init__(self, n_bytes):
                self.bytes_left = n_bytes

            def __call__(self):
                b = f.read(min(self.bytes_left, buffer_size))
                self.bytes_left -= len(b)
                return b

        start, end = content_range
        f.seek(start)
        get_bytes = ByteReader(end - start)

    else:
        def get_bytes():
            return f.read(buffer_size)

    try:
        buf = get_bytes()
        while buf:
            yield buf
            buf = get_bytes()
    finally:
        f.close()
