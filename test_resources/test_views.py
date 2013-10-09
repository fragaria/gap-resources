from gap.utils.tests import WebAppTestBase

from resources.resource import resource_for_model

from app.example_module.models import ExampleModel


Resource = resource_for_model(ExampleModel)


class TestViews(WebAppTestBase):
    def test_root(self):
        resp = self.get('/resources/example-model')
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.content_type, 'application/json')

    def test_describe(self):
        resp = self.get('/resources/example-model/describe', status=404)
        #self.assertEquals(resp.status_code, 200)
        #self.assertEquals(resp.content_type, 'application/json')
        print resp.body
        self.assertEqual(resp.json, Resource.describe())
