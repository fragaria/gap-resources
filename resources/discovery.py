from google.appengine.ext import ndb

from gap.utils.imports import import_class

from register import register


def discover_models(modules):
    for module in modules:
        module = import_class(module)

        for model in [m for m in module.__dict__.values() if isinstance(m, ndb.model.MetaModel)]:
            register(model)

