from google.appengine.ext import ndb

__all__ = ['NamespaceModel']


class NamespaceModel(ndb.Model):
    """ Datastore namespace """
    name = ndb.StringProperty(indexed=True, required=True)
    description = ndb.StringProperty(required=False)
    disabled = ndb.BooleanProperty(default=False)

    @classmethod
    def create(cls, name, description=None):
        namespace = NamespaceModel(name=name, description=description)
        namespace.put()
