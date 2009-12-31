from __future__ import with_statement

import unittest

class SkinTests(unittest.TestCase):
    def setUp(self):
        import os
        import sys
        import tempfile
        tmpdir = tempfile.mkdtemp('_happy_test')
        with open(os.path.join(tmpdir, 'test1.txt'), 'w') as f:
            print >>f, "I'm overriding your test."

        self.tmpdir = tmpdir

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _make_one(self, *layers):
        from happy.skin import Skin
        return Skin(*layers)

    def test_package_resource(self):
        skin = self._make_one('happy.tests')
        self.assertEqual(skin.lookup('test2.txt'), None)

        resource = skin.lookup('test1.txt')
        self.assertEqual(resource.stream().read(), 'Test One.\n')
        self.assertEqual(resource.string(), 'Test One.\n')

        import os
        import sys
        here = os.path.dirname(sys.modules[__name__].__file__)
        self.assertEqual(resource.abspath(), os.path.join(here, 'test1.txt'))

        self.assertEqual(skin.lookup('fixture/test2.txt').string(),
                         'Test Two.\n')

    def test_filesystem_resource(self):
        import os
        skin = self._make_one(self.tmpdir)
        resource = skin.lookup('test1.txt')
        self.assertEqual(resource.stream().read(),
                         "I'm overriding your test.\n")
        self.assertEqual(resource.string(), "I'm overriding your test.\n")
        self.assertEqual(resource.abspath(),
                         os.path.join(self.tmpdir, 'test1.txt'))

    def test_package_w_subdir(self):
        skin = self._make_one('happy.tests:fixture')
        self.assertEqual(skin.lookup('test1.txt'), None)
        self.assertEqual(skin.lookup('test2.txt').string(), 'Test Two.\n')

    def test_override(self):
        skin = self._make_one()
        skin.add_layer('happy.tests')
        skin.add_layer(self.tmpdir)
        self.assertEqual(skin.lookup('test1.txt').string(),
                         "I'm overriding your test.\n")
        self.assertEqual(skin.lookup('fixture/test2.txt').string(),
                         "Test Two.\n")

    def test_package_listdir(self):
        skin = self._make_one('happy.tests')
        self.failUnless(skin.lookup('').isdir())
        self.failUnless(skin.lookup('fixture').isdir())
        self.assertEqual(skin.lookup('fixture').listdir(), ['test2.txt'])

    def test_filesystem_listdir(self):
        skin = self._make_one(self.tmpdir)
        self.failUnless(skin.lookup('').isdir())
        self.assertEqual(skin.lookup('').listdir(), ['test1.txt'])

class TestSkinApplication(unittest.TestCase):
    def test_it(self):
        from happy.skin import Skin
        from happy.skin import SkinApplication
        skin = Skin('happy.tests')
        app = SkinApplication(skin)

        import webob
        request = webob.Request.blank
        self.assertEqual(app(request('/')), None)
        self.assertEqual(app(request('/test1.txt')).body, 'Test One.\n')

    def test_override_directory_index_view(self):
        from happy.skin import Skin
        from happy.skin import SkinApplication

        class MyApp(SkinApplication):
            def index_directory(self, request, resource):
                return 'Howdy'

        import webob
        request = webob.Request.blank
        skin = Skin('happy.tests')
        app = MyApp(skin)

        self.assertEqual(app(request('/')), 'Howdy')
        self.assertEqual(app(request('/test1.txt')).body, 'Test One.\n')
        self.assertEqual(app(request('/foo')), None)
