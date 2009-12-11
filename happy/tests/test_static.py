import unittest

class TestFileResponse(unittest.TestCase):
    fpath = None
    def _mktestfile(self, size=32, ext='.txt'):
        # Dump some binary data in a temporary file for testing
        import os
        import tempfile
        fd, self.fpath = tempfile.mkstemp(ext)
        f = os.fdopen(fd, 'wb')
        for i in xrange(size):
            f.write(chr(i%0x100))
        f.close()

        return self.fpath

    def tearDown(self):
        if self.fpath is not None:
            import os
            os.remove(self.fpath)
            self.fpath = None

    def test_it(self):
        from happy.static import FileResponse
        fpath = self._mktestfile(80000)
        expected = open(fpath, 'rb').read()
        response = FileResponse(fpath)
        body = ''.join(response.app_iter)
        self.assertEqual(body, expected)
        self.assertEqual(response.content_length, len(expected))
        self.assertEqual(response.content_type, 'text/plain')

    def test_mime_type(self):
        from happy.static import FileResponse
        fpath = self._mktestfile(ext='.pdf')
        response = FileResponse(fpath)
        self.assertEqual(response.content_type, 'application/pdf')

    def test_buffer_size(self):
        from happy.static import FileResponse
        fpath = self._mktestfile(10100)
        response = FileResponse(fpath, buffer_size=1000)
        bufs = list(response.app_iter)
        self.assertEqual(len(bufs), 11)
        self.assertEqual(len(bufs[0]), 1000)
        self.assertEqual(len(bufs[-1]), 100)

    def test_modified(self):
        from happy.static import FileResponse
        from happy.static import ISO_1123
        import datetime
        import os
        fpath = self._mktestfile()
        response = FileResponse(fpath)
        expected = datetime.datetime.utcfromtimestamp(os.path.getmtime(fpath))
        mtime = datetime.datetime.strptime(
            response.headers['Last-Modified'], ISO_1123)
        self.assertEqual(mtime, expected)

    def test_not_modified(self):
        from happy.static import FileResponse
        import webob
        fpath = self._mktestfile()
        request = webob.Request.blank('/')
        response = FileResponse(fpath, request)
        last_modified = response.last_modified
        request.if_modified_since = last_modified
        response = FileResponse(fpath, request)
        self.assertEqual(response.status_int, 304)
