from google.appengine.ext import ndb

from gap.utils.imports import import_class

from register import register
from resources.resource import Resource


def discover_models(modules):
    for module in modules:
        module = import_class(module)

        if module.__class__ == 'module':
            for model in [m for m in module.__dict__.values() if isinstance(m, ndb.model.MetaModel)]:
                register(model)
        elif isinstance(module, ndb.model.MetaModel):  # the module is actualy a model
            register(module)
        elif issubclass(module, Resource):
            register(module.model, module)
        else:
            raise TypeError("Expected modul, resource or model but got %s.%s" % (module.__module__, module.__class__.__name__))

