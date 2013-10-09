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

