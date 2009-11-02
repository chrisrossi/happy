import unittest

class TraversalTests(unittest.TestCase):
    def test_traverse(self):
        from happy.traversal import traverse as f
        root = DummyModel()
        a = root['a'] = DummyModel()
        b = root['b'] = DummyModel()
        c = b['c'] = DummyModel()
        d = a['d'] = object()
        e = root['e'] = DummyModel()
        g = e['g'] = DummyModel()
        h = e['h'] = DummyModel()

        self.assertEqual(f(root, ''), (root, []))
        self.assertEqual(f(root, '/'), (root, []))
        self.assertEqual(f(root, '/a'), (a, []))
        self.assertEqual(f(root, '/a/'), (a, []))
        self.assertEqual(f(root, '/a/d/f'), (d, ['f']))
        self.assertEqual(f(root, '/b/c'), (c, []))
        self.assertEqual(f(root, '/b/c/d/e'), (c, ['d', 'e']))
        self.assertNotEqual(f(root, '/e/g'), (h, []))

class DummyModel(dict):
    def __eq__(self, other):
        return self is other
