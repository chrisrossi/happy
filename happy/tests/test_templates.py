import unittest

class TestTemplates(unittest.TestCase):
    def _make_one(self, rendered=u'Howdy'):
        from happy.skin import Skin
        from happy.templates import Templates
        skin = Skin('happy.tests')
        return Templates(skin, DummyTemplateFactory(rendered))

    def test_unicode(self):
        templates = self._make_one()
        response = templates.render_to_response('test1.txt', foo='foo')
        self.assertEqual(response.body, 'Howdy')
        self.failIf(isinstance(response.body, unicode))
        self.assertEqual(response.charset, 'UTF-8')
        self.assertEqual(response.content_type, 'text/html')

    def test_not_unicode(self):
        templates = self._make_one('Howdy')
        response = templates.render_to_response('test1.txt', foo='foo')
        self.assertEqual(response.body, 'Howdy')
        self.failIf(isinstance(response.body, unicode))
        self.assertEqual(response.charset, None)
        self.assertEqual(response.content_type, 'text/html')

    def test_register_extension(self):
        templates = self._make_one()
        templates.register_factory('py', DummyTemplateFactory(u'Sneeze'))
        self.assertEqual(templates.render('test1.txt'), 'Howdy')
        self.assertEqual(templates.render('test_templates.py'), 'Sneeze')

    def test_missing_template(self):
        templates = self._make_one()
        self.assertRaises(KeyError, templates.render, 'foo.bar')

class DummyTemplateFactory(object):
    def __init__(self, rendered):
        self.rendered = rendered

    def __call__(self, fname):
        import os
        assert os.path.exists(fname)
        def render(**kw):
            return self.rendered
        return render
