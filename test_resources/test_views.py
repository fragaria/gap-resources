from gap.utils.tests import WebAppTestBase

from resources.resource import resource_for_model

from app.example_module.models import ExampleModel


Resource = resource_for_model(ExampleModel)


class TestViews(WebAppTestBase):
    def test_root(self):
        resp = self.get('/resources/example-model')
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.content_type, 'application/json')
        self.assertEqual(resp.json, {
            'model': 'ExampleModel',
            'count': 0,
            'objects': []
        })

    def test_trailing_slashes(self):
        resp0 = self.get('/resources/example-model')
        resp1 = self.get('/resources/example-model/')
        self.assertEqual(resp0.json, resp1.json)

    def test_describe(self):
        resp = self.get('/resources/example-model/describe')
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.content_type, 'application/json')
        self.assertEqual(resp.json, Resource.describe())

    def test_list(self):
        e1 = ExampleModel.create(method='import_all')
        e2 = ExampleModel.create(method='import_changes')

        e1.put()
        e2.put()

        resp = self.get('/resources/example-model')
        self.assertEquals(resp.content_type, 'application/json')
        self.assertEqual(resp.json, Resource.list())

        e1.key.delete()
        e2.key.delete()

    def test_get(self):
        e = ExampleModel.create(method='import_all')
        e.put()

        resp = self.get('/resources/example-model/%s' % e.key.id())
        self.assertEquals(resp.content_type, 'application/json')
        self.assertEquals(resp.json, Resource.get(e.key.id()))

        e.key.delete()
