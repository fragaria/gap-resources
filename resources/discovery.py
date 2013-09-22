from google.appengine.ext import ndb
from register import register

def discover_models(moduls):
    from gap.utils.imports import import_class

    for modul in moduls:
        modul = import_class(modul)
        models  = [ m for m in modul.__dict__.values() if isinstance(m, ndb.model.MetaModel) ]
        for model in models:
            register(model)

