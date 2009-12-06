import unittest

class AdaptationManagerTests(unittest.TestCase):
    def _make_one(self):
        from happy.adaptation import AdaptationManager
        return AdaptationManager()

    def test_it(self):
        class A(object):
            pass

        class C(A):
            pass

        class Interface(object):
            pass

        class AdapterA(object):
            def __init__(self, a):
                self.a = a

        class AdapterC(object):
            def __init__(self, c):
                self.c = c

        manager = self._make_one()
        manager.register(AdapterA, A, Interface)

        obj = C()
        adapted = manager.adapt(obj, Interface)
        self.assertEqual(adapted.a, obj)

        manager.register(AdapterC, C, Interface)
        adapted = manager.adapt(obj, Interface)
        self.assertEqual(adapted.c, obj)

        obj = A()
        adapted = manager.adapt(obj, Interface)
        self.assertEqual(adapted.a, obj)

        self.assertRaises(KeyError, manager.adapt, obj, object)
        self.assertRaises(KeyError, manager.adapt, object(), Interface)
