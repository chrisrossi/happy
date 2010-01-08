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
        import datetime
        import os
        fpath = self._mktestfile()
        response = FileResponse(fpath)
        expected = datetime.datetime.utcfromtimestamp(os.path.getmtime(fpath))
        expected = str(expected) + "+00:00"
        self.assertEqual(str(response.last_modified), expected)

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
        self.assertEqual(response.body, '')

    def test_expires(self):
        from happy.static import FileResponse
        fpath = self._mktestfile()
        response = FileResponse(fpath)
        self.assertEqual(response.expires, response.date)

        from datetime import timedelta
        response = FileResponse(fpath, expires_timedelta=timedelta(days=1))
        self.assertEqual(response.expires, response.date + timedelta(days=1))

    def test_range(self):
        from happy.static import FileResponse
        import webob
        fpath = self._mktestfile(800)
        request = webob.Request.blank('/')
        request.headers['Range'] = 'bytes=0-99'
        response = FileResponse(fpath, request)
        body = ''.join(list(response.app_iter))
        self.assertEqual(len(body), 100)
        self.assertEqual(ord(body[0]), 0)
        self.assertEqual(response.status, '206 Partial Content')

        request = webob.Request.blank('/')
        request.headers['Range'] = 'bytes=-200'
        response = FileResponse(fpath, request)
        body = ''.join(list(response.app_iter))
        self.assertEqual(len(body), 200)
        self.assertEqual(ord(body[0]), 600 % 0x100)
        self.assertEqual(response.status_int, 206)

        expected = open(fpath, 'rb').read()
        ranges = [
            'bytes=0-99',
            'bytes=100-449',
            'bytes=450-699',
            'bytes=-100',
            ]
        for i in xrange(len(ranges)):
            request = webob.Request.blank('/')
            request.headers['Range'] = ranges[i]
            response = FileResponse(fpath, request)
            body = ''.join(list(response.app_iter))
            ranges[i] = body
        got = ''.join(ranges)

        self.assertEqual(got, expected)

    def test_multiple_ranges_not_supported(self):
        from happy.static import FileResponse
        import webob
        fpath = self._mktestfile(800)
        request = webob.Request.blank('/')
        request.headers['Range'] = 'bytes=0-99,150-199'
        response = FileResponse(fpath, request)
        self.assertEqual(len(response.body), 800)
        self.assertEqual(response.status_int, 200)

    def test_other_range_units_not_supported(self):
        from happy.static import FileResponse
        import webob
        fpath = self._mktestfile(800)
        request = webob.Request.blank('/')
        request.headers['Range'] = 'grams=0-99'
        response = FileResponse(fpath, request)
        self.assertEqual(len(response.body), 800)
        self.assertEqual(response.status_int, 200)

    def test_bad_range(self):
        from happy.static import FileResponse
        import webob
        fpath = self._mktestfile(800)
        request = webob.Request.blank('/')
        request.headers['Range'] = 'bytes=800-899'
        response = FileResponse(fpath, request)
        self.assertEqual(len(response.body), 0)
        self.assertEqual(response.status,
                         '416 Requested Range Not Satisfiable')

class TestDirectoryApplication(unittest.TestCase):
    def setUp(self):
        import os
        import tempfile
        self.folder = tempfile.mkdtemp()
        fname = os.path.join(self.folder, 'foo.txt')
        open(fname, 'w').write('foo\n')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.folder)

    def test_it(self):
        from happy.static import DirectoryApplication
        import webob
        app = DirectoryApplication(self.folder)
        request = webob.Request.blank

        self.assertEqual(app(request('/')), None)
        self.assertEqual(app(request('/foo.txt')).body, 'foo\n')

    def test_override_directory_index_view(self):
        from happy.static import DirectoryApplication
        class MyApp(DirectoryApplication):
            def index_directory(self, request):
                return 'Howdy'

        import webob
        request = webob.Request.blank
        app = MyApp(self.folder)

        self.assertEqual(app(request('/')), 'Howdy')
        self.assertEqual(app(request('/foo.txt')).body, 'foo\n')
        self.assertEqual(app(request('/foo')), None)
