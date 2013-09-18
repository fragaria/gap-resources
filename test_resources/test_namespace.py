from unittest import TestCase
import json
import logging
import webtest

from google.appengine.api import namespace_manager
from google.appengine.ext import testbed, ndb
import webapp2

from resources import register
from resources.namespace import NamespaceModel
from resources.resource import resource_for_model
from views import NamespaceHandler
from webtest.app import AppError


class TestModel(ndb.Model):
    """ TestModel description """
    value = ndb.StringProperty(required=False)


NamespaceResource = resource_for_model(NamespaceModel)


class TestNamespace(TestCase):
    def setUp(self):
        logging.getLogger().setLevel(logging.ERROR)

        # Begin with testbed instance
        self.testbed = testbed.Testbed()

        # Activate the testbed environment, this will prepare the service stubs
        self.testbed.activate()

        # Select all the needed service stubs
        self.testbed.init_datastore_v3_stub(datastore_file='/tmp/datastore.sqlite', use_sqlite=True)
        self.testbed.init_memcache_stub()

        # Clear the datastore
        stub = self.testbed.get_stub('datastore_v3')
        stub.Clear()

        for k in NamespaceModel.query().fetch(keys_only=True):
            k.delete()

        register.register(NamespaceModel)

        app = webapp2.WSGIApplication([
            ('/namespace', NamespaceHandler),
            ('/namespace/([^\/\?]*)', NamespaceHandler),
            ('/namespace/([^\/]*)/([^\/\?]*)', NamespaceHandler),
        ])
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        self.testbed.deactivate()

        register.unregister(NamespaceModel)

    def _create_namespace(self, name):
        namespace_manager.set_namespace(name)
        # There has to be created at least one entity after creating new namespace
        TestModel(value='test').put()

    def test_describe(self):
        self.testapp.get('/namespace/describe')

    def test_get_current_default_namespace(self):
        current_namespace_response = self.testapp.get('/namespace/get')
        self.assertEqual('""', current_namespace_response.body)

    def test_get_current_default_namespace(self):
        name = 'test_namespace'
        self._create_namespace(name)
        current_namespace_response = self.testapp.get('/namespace/get')
        self.assertEqual('"%s"' % name, current_namespace_response.body)

    def test_list_only_default_namespace(self):
        available_namespaces_response = self.testapp.get('/namespace')
        self.assertEqual('[""]', available_namespaces_response.body)

    def test_list_namespaces(self):
        name_1 = 'test_namespace_1'
        self._create_namespace(name_1)
        name_2 = 'test_namespace_2'
        self._create_namespace(name_2)
        available_namespaces_response = self.testapp.get('/namespace')
        self.assertEqual('["", "%s", "%s"]' % (name_1, name_2), available_namespaces_response.body)

    def test_query_not_existing_namespace(self):
        name = 'test_namespace'
        try:
            self.testapp.get('/namespace/query?name=%s' % name)
        except AppError, e:
            self.assertTrue('404' in e.message)

    def test_query_existing_namespace(self):
        name = 'test_namespace'
        self._create_namespace(name)
        self.testapp.get('/namespace/query?name=%s' % name)

    def test_namespace_not_existing(self):
        name = 'test_namespace'
        try:
            self.testapp.get('/namespace/%s/list' % name)
        except AppError, e:
            self.assertTrue('404' in e.message)

    def test_namespace_describe(self):
        name = 'test_namespace'
        self._create_namespace(name)
        description_response = self.testapp.get('/namespace/%s/describe' % name)
        description = json.loads(description_response.body)
        self.assertTrue('bytes' in description)
        self.assertTrue('count' in description)
        self.assertTrue('timestamp' in description)

    def test_namespace_list(self):
        name = 'test_namespace'
        self._create_namespace(name)
        list_response = self.testapp.get('/namespace/%s/list' % name)
        self.assertTrue('TestModel' in list_response)
