import unittest

class TestEventManager(unittest.TestCase):
    def make_one(self):
        from happy.event import EventManager as cut
        return cut()

    def test_simple(self):
        events = self.make_one()
        handler = DummyHandler()
        events.register(DummyEvent, handler)
        event = DummyEvent()
        events.notify(event)
        self.assertEqual(handler.handled, [event,])

    def test_unregister(self):
        events = self.make_one()
        handler = DummyHandler()
        events.register(DummyEvent, handler)
        event = DummyEvent()
        events.notify(event)
        self.assertEqual(handler.handled, [event,])

        handler.handled = []
        events.unregister(DummyEvent, handler)
        events.notify(event)
        self.assertEqual(handler.handled, [])

        self.assertRaises(ValueError, events.unregister, DummyEvent, handler)

    def test_multiple_handlers(self):
        events = self.make_one()
        handler1 = DummyHandler()
        events.register(DummyEvent, handler1)
        handler2 = DummyHandler()
        events.register(DummyEvent, handler2)
        event = DummyEvent()
        events.notify(event)
        self.assertEqual(handler1.handled, [event,])
        self.assertEqual(handler2.handled, [event,])

    def test_unregister_w_multiple_handlers(self):
        events = self.make_one()
        handler1 = DummyHandler()
        events.register(DummyEvent, handler1)
        handler2 = DummyHandler()
        events.register(DummyEvent, handler2)
        event = DummyEvent()
        events.notify(event)
        self.assertEqual(handler1.handled, [event,])
        self.assertEqual(handler2.handled, [event,])

        events.unregister(DummyEvent, handler2)
        events.notify(event)
        self.assertEqual(handler1.handled, [event, event])
        self.assertEqual(handler2.handled, [event,])

        self.assertRaises(ValueError, events.unregister, DummyEvent, handler2)

    def test_event_inheritance(self):
        events = self.make_one()
        handler1 = DummyHandler()
        events.register(DummyBaseEvent, handler1)
        handler2 = DummyHandler()
        events.register(DummyEvent, handler2)
        event = DummyEvent()
        events.notify(event)
        self.assertEqual(handler1.handled, [event,])
        self.assertEqual(handler2.handled, [event,])

        event2 = DummyBaseEvent()
        events.notify(event2)
        self.assertEqual(handler1.handled, [event, event2])
        self.assertEqual(handler2.handled, [event,])

class DummyBaseEvent(object):
    pass

class DummyEvent(DummyBaseEvent):
    pass

class DummyHandler(object):
    def __init__(self):
        self.handled = []

    def __call__(self, event):
        self.handled.append(event)
