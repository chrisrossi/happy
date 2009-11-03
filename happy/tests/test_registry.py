import unittest

class RegistryTests(unittest.TestCase):
    def test_one_axis_no_specificity(self):
        from happy.registry import Registry
        from happy.registry import IdentityAxis
        registry = Registry(IdentityAxis())
        a = object()
        b = object()
        registry.register(a)
        registry.register(b, 'foo')

        self.assertEqual(registry.lookup(), a)
        self.assertEqual(registry.lookup('foo'), b)
        self.assertEqual(registry.lookup('bar'), None)

    def test_two_axes(self):
        from happy.registry import Registry
        from happy.registry import IdentityAxis
        from happy.registry import MROAxis
        registry = Registry(MROAxis(), IdentityAxis())

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
        from happy.registry import IdentityAxis
        registry = Registry(IdentityAxis)
        self.assertRaises(ValueError, registry.register, object(),
                          'one', 'two')

    def test_lookup_too_many_keys(self):
        from happy.registry import Registry
        from happy.registry import IdentityAxis
        registry = Registry(IdentityAxis)
        self.assertRaises(ValueError, registry.lookup, 'one', 'two')

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
