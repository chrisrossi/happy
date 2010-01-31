import unittest

class RegistryTests(unittest.TestCase):
    def test_one_axis_no_specificity(self):
        from happy.registry import Registry
        from happy.registry import SimpleAxis
        registry = Registry(('foo', SimpleAxis()))
        a = object()
        b = object()
        registry.register(a)
        registry.register(b, 'foo')

        self.assertEqual(registry.lookup(), a)
        self.assertEqual(registry.lookup('foo'), b)
        self.assertEqual(registry.lookup('bar'), None)

    def test_two_axes(self):
        from happy.registry import Registry
        from happy.registry import SimpleAxis
        from happy.registry import TypeAxis
        registry = Registry(('type', TypeAxis()),
                            ('name', SimpleAxis()))

        target1 = Target('one')
        registry.register(target1, object)

        target2 = Target('two')
        registry.register(target2, DummyA)

        target3 = Target('three')
        registry.register(target3, DummyA, 'foo')

        context1 = object()
        self.assertEqual(registry.lookup(context1), target1)

        context2 = DummyB()
        self.assertEqual(registry.lookup(context2), target2)
        self.assertEqual(registry.lookup(context2, 'foo'), target3)

        target4 = object()
        registry.register(target4, DummyB)

        self.assertEqual(registry.lookup(context2), target4)
        self.assertEqual(registry.lookup(context2, 'foo'), target3)

    def test_register_too_many_keys(self):
        from happy.registry import Registry
        from happy.registry import SimpleAxis
        registry = Registry(('name', SimpleAxis()))
        self.assertRaises(ValueError, registry.register, object(),
                          'one', 'two')

    def test_lookup_too_many_keys(self):
        from happy.registry import Registry
        from happy.registry import SimpleAxis
        registry = Registry(('name', SimpleAxis()))
        self.assertRaises(ValueError, registry.lookup, 'one', 'two')

    def test_conflict_error(self):
        from happy.registry import Registry
        from happy.registry import SimpleAxis
        registry = Registry(('name', SimpleAxis()))
        registry.register(object(), name='foo')
        self.assertRaises(ValueError, registry.register, object(), 'foo')

    def test_override(self):
        from happy.registry import Registry
        from happy.registry import SimpleAxis
        registry = Registry(('name', SimpleAxis()))
        registry.register(1, name='foo')
        registry.override(2, name='foo')
        self.assertEqual(registry.lookup('foo'), 2)

    def test_skip_nodes(self):
        from happy.registry import Registry
        from happy.registry import SimpleAxis
        registry = Registry(
            ('one', SimpleAxis()),
            ('two', SimpleAxis()),
            ('three', SimpleAxis())
            )
        registry.register('foo', one=1, three=3)
        self.assertEqual(registry.lookup(1, three=3), 'foo')

    def test_miss(self):
        from happy.registry import Registry
        from happy.registry import SimpleAxis
        registry = Registry(
            ('one', SimpleAxis()),
            ('two', SimpleAxis()),
            ('three', SimpleAxis())
            )
        registry.register('foo', 1, 2)
        self.assertEqual(registry.lookup(one=1, three=3), None)

    def test_bad_lookup(self):
        from happy.registry import Registry
        from happy.registry import SimpleAxis
        registry = Registry(('name', SimpleAxis()),
                            ('grade', SimpleAxis()))
        self.assertRaises(ValueError, registry.register, 1, foo=1)
        self.assertRaises(ValueError, registry.lookup, foo=1)
        self.assertRaises(ValueError, registry.register, 1, 'foo', name='foo')

class TestBaseAxis(unittest.TestCase):
    def test_abstract_method(self):
        from happy.registry import BaseAxis
        axis = BaseAxis()
        self.assertRaises(NotImplementedError, axis.get_keys, None)

class DummyA(object):
    pass

class DummyB(DummyA):
    pass

class Target(object):
    def __init__(self, name):
        self.name = name

    # Only called if being printed due to a failing test
    def __repr__(self): #pragma NO COVERAGE
        return "Target('%s')" % self.name
