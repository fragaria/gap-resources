from unittest import TestCase

from google.appengine.ext import ndb


from resources import register

from app.example_module.models import ExampleModel


class MockModel(ndb.Model):
    pass


class TestUtils(TestCase):
    def test_get_models(self):
        self.assertEqual(False, register.is_registered(MockModel))
        self.assertEqual([ExampleModel], register.models())

        register.register(MockModel)
        self.assertEqual(True, register.is_registered(MockModel))
        self.assertEqual([ExampleModel, MockModel], register.models())

        register.unregister(MockModel)
        self.assertEqual(False, register.is_registered(MockModel))
        self.assertEqual([ExampleModel], register.models())

    def test_repr(self):
        register.register(MockModel)
        self.assertEqual('<ModelRegistry: ExampleModel,MockModel>', repr(register))
        register.unregister(MockModel)

    def test_already_registered(self):
        self.assertRaises(register.AlreadyRegistered, lambda: register.register(ExampleModel))

    def test_not_registered(self):
        self.assertRaises(register.NotRegistered, lambda: register.unregister(MockModel))

    def test_register_takes_only_resourcehandler_or_resource_subclasses(self):
        self.assertRaises(ValueError, lambda: register.register(MockModel, handler_or_resource=object))
