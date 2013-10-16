from google.appengine.ext import ndb

__author__ = 'xaralis'


class ExampleModel(ndb.Model):
    # key name = user email
    method = ndb.StringProperty(indexed=False, required=True,
                                choices=('import_all', 'import_changes'))
    lastChangeId = ndb.IntegerProperty(indexed=True, required=False)
    now = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def create(cls, **kwargs):
        params = {
            'method': 'import_all'
        }

        if kwargs:
            params.update(kwargs)

        return cls(**params)
