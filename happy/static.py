import mimetypes
import os
import webob

DEFAULT_BUFFER_SIZE = 1<<16 # 64 kilobytes

class FileResponse(webob.Response):
    """
    Serves a file from the filesystem.
    """
    def __init__(self, path, buffer_size=DEFAULT_BUFFER_SIZE):
        super(FileResponse, self).__init__()
        self.path = path
        self.buffer_size = buffer_size

        self.content_length = os.path.getsize(path)
        self.content_type = mimetypes.guess_type(path, strict=False)[0]

    @property
    def app_iter(self):
        buffer_size = self.buffer_size
        f = open(self.path, 'rb')
        try:
            buf = f.read(buffer_size)
            while buf:
                yield buf
                buf = f.read(buffer_size)
        finally:
            f.close()
