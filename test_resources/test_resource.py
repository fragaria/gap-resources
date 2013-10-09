from datetime import datetime, timedelta
from unittest import TestCase
import logging
import time

from google.appengine.ext import ndb, testbed

from resources import register
from resources.resource import resource_for_model


class TestModel(ndb.Model):
    datetimeProperty = ndb.DateTimeProperty(indexed=True, required=False)
    stringProperty = ndb.StringProperty(required=False, verbose_name=u'My cool stringProperty')
    integerProperty = ndb.IntegerProperty(required=False, indexed=False)
    requiredProperty = ndb.IntegerProperty(required=True, indexed=True)


class TestKeyModel(ndb.Model):
    keyProperty = ndb.KeyProperty(kind=TestModel)


class TestStructuredPropertyModel(ndb.Model):
    structuredProperty = ndb.StructuredProperty(TestModel, repeated=True)


Resource = resource_for_model(TestModel)
KeyResource = resource_for_model(TestKeyModel)
StructuredResource = resource_for_model(TestStructuredPropertyModel)


def _create_instance(req, **kwargs):
    attrs = {
        'requiredProperty': req,
        'datetimeProperty': datetime.now()
    }
    attrs.update(kwargs)

    i = TestModel(**attrs)
    i.put()

    return i


class TestResource(TestCase):
    def setUp(self):
        logging.getLogger().setLevel(logging.ERROR)

        # Begin with testbed instance
        self.testbed = testbed.Testbed()

        # Activate the testbed environment, this will prepare the service stubs
        self.testbed.activate()

        # Select all the needed service stubs
        self.testbed.init_datastore_v3_stub(datastore_file='/tmp/datastore.sqlite', use_sqlite=True)
        self.testbed.init_memcache_stub()

        for k in TestModel.query().fetch(keys_only=True):
            k.delete()

        for k in TestKeyModel.query().fetch(keys_only=True):
            k.delete()

        for k in TestStructuredPropertyModel.query().fetch(keys_only=True):
            k.delete()

        register.register(TestModel)
        register.register(TestKeyModel)
        register.register(TestStructuredPropertyModel)

    def tearDown(self):
        self.testbed.deactivate()

        register.unregister(TestModel)
        register.unregister(TestKeyModel)
        register.unregister(TestStructuredPropertyModel)

    def test_as_dict(self):
        now = datetime.now()
        inst = _create_instance(0, datetimeProperty=now)

        self.assertEqual(Resource(inst).as_dict(), {
            'model': 'TestModel',
            'datetimeProperty': int(time.mktime(now.timetuple())) * 1000,
            'stringProperty': None,
            'integerProperty': None,
            'requiredProperty': 0,
            'id': inst.key.id()
        })

    def test_get(self):
        inst = _create_instance(0)
        # Valid id
        self.assertEqual(Resource.get(inst.key.id()), Resource(inst).as_dict())
        # Invalid id
        self.assertEqual(Resource.get(0), None)

    def test_create(self):
        inst_dict = Resource.create({
            'requiredProperty': 1,
            'datetimeProperty': 1381307680000
        })

        self.assertEqual(inst_dict, Resource.get(inst_dict['id']))

    def test_update(self):
        now = datetime.now()
        not_now = datetime.now() + timedelta(days=1)
        not_now_stamp = int(time.mktime(not_now.timetuple())) * 1000

        inst = _create_instance(0, datetimeProperty=now)
        inst.datetimeProperty = not_now

        old_updated = Resource(inst).as_dict()
        new = Resource.update(inst.key.id(), {'datetimeProperty': not_now_stamp})

        self.assertEqual(new, old_updated)

        # Not existent id
        self.assertEqual(Resource.update(0, {'datetimeProperty': not_now_stamp}), None)

    def test_delete(self):
        id = _create_instance(0).key.id()

        self.assertTrue(TestModel.get_by_id(id) is not None)
        self.assertTrue(Resource.delete(id))
        self.assertTrue(TestModel.get_by_id(id) is None)
        self.assertFalse(Resource.delete(id))

    def test_describe(self):
        self.assertEqual(Resource.describe(), {
            'model': 'TestModel',
            'fields': {
                'datetimeProperty': {'type': 'datetime', 'verbose_name': 'datetimeProperty', 'required': False, 'indexed': True, 'repeated': False},
                'stringProperty': {'type': 'string', 'verbose_name': u'My cool stringProperty', 'required': False, 'indexed': True, 'repeated': False},
                'integerProperty': {'type': 'integer', 'verbose_name': 'integerProperty', 'required': False, 'indexed': False, 'repeated': False},
                'requiredProperty': {'type': 'integer', 'verbose_name': 'requiredProperty', 'required': True, 'indexed': True, 'repeated': False},
            }
        })

    def test_list(self):
        self.maxDiff = None

        i1 = _create_instance(0)
        i2 = _create_instance(1)

        self.assertEqual(Resource.list(), {
            'model': 'TestModel',
            'count': 2,
            'objects': [Resource(i1).as_dict(include_class_info=False),
                        Resource(i2).as_dict(include_class_info=False)]
        })

    def test_query_filters(self):
        self.maxDiff = None

        i1 = _create_instance(0, datetimeProperty=datetime(2012, 1, 1))
        i2 = _create_instance(1)

        self.assertEqual(Resource.query(requiredProperty=1), {
            'model': 'TestModel',
            'count': 1,
            'objects': [Resource(i2).as_dict(include_class_info=False)]
        })

        # Cannot filter on non-indexed
        self.assertRaises(Resource.InvalidFilter, lambda: Resource.query(integerProperty=1))

        # Cannot filter on uknown
        self.assertRaises(Resource.InvalidFilter, lambda: Resource.query(integerPropertyas=1))

        # Provide timestamp when filtering on dates
        self.assertEqual(Resource.query(datetimeProperty=int(time.mktime(i1.datetimeProperty.timetuple())) * 1000), {
            'model': 'TestModel',
            'count': 1,
            'objects': [Resource(i1).as_dict(include_class_info=False)]
        })

    def test_query_orders(self):
        self.maxDiff = None

        i1 = _create_instance(0, datetimeProperty=datetime(2012, 1, 1))
        i2 = _create_instance(1, datetimeProperty=datetime(2013, 1, 1))

        self.assertEqual(Resource.query(ordering='datetimeProperty'), {
            'model': 'TestModel',
            'count': 2,
            'objects': [Resource(i1).as_dict(include_class_info=False),
                        Resource(i2).as_dict(include_class_info=False)]
        })

        self.assertEqual(Resource.query(ordering='-datetimeProperty'), {
            'model': 'TestModel',
            'count': 2,
            'objects': [Resource(i2).as_dict(include_class_info=False),
                        Resource(i1).as_dict(include_class_info=False)]
        })

        i3 = _create_instance(2, datetimeProperty=datetime(2013, 1, 1))

        self.assertEqual(Resource.query(ordering=['-datetimeProperty', 'requiredProperty']), {
            'model': 'TestModel',
            'count': 3,
            'objects': [Resource(i2).as_dict(include_class_info=False),
                        Resource(i3).as_dict(include_class_info=False),
                        Resource(i1).as_dict(include_class_info=False)]
        })

        # Cannot query on non-indexed
        self.assertRaises(Resource.InvalidOrderingProperty, lambda: Resource.query(ordering='integerProperty'))

        # Cannot query on uknown
        self.assertRaises(Resource.InvalidOrderingProperty, lambda: Resource.query(ordering='asdasdad'))

    def test_key_nospan(self):
        inst = _create_instance(0)
        kinst = TestKeyModel(keyProperty=inst.key)
        kinst.put()

        self.assertEqual(KeyResource(kinst).as_dict(), {
            'model': 'TestKeyModel',
            'keyProperty': {'id': inst.key.id(), 'model': 'TestModel'},
            'id': kinst.key.id()
        })

    def test_key_span(self):
        self.maxDiff = None

        inst = _create_instance(0)
        kinst = TestKeyModel(keyProperty=inst.key)
        kinst.put()

        self.assertEqual(KeyResource(kinst).as_dict(span_keys=['keyProperty']), {
            'model': 'TestKeyModel',
            'keyProperty': Resource(inst).as_dict(),
            'id': kinst.key.id()
        })

    def test_structuredproperties(self):
        i1 = _create_instance(0)
        i2 = _create_instance(1)

        sinst = TestStructuredPropertyModel(structuredProperty=[i1, i2])
        sinst.put()

        self.assertEqual(StructuredResource(sinst).as_dict(), {
            'model': 'TestStructuredPropertyModel',
            'structuredProperty': [Resource(i1).as_dict(), Resource(i2).as_dict()],
            'id': sinst.key.id()
        })
