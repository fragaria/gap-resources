from datetime import date, datetime
import time
from functools import partial

from google.appengine.api.datastore_errors import BadFilterError, BadValueError

__all__ = ['Resource', 'resource_for_model']


def _v(if_none_func, v):
    if v is None:
        return None
    return if_none_func(v)


def _val(map, prop, val):
    propname = prop.__class__.__name__
    return map[propname](val) if propname in map else val


val_from_str = partial(_val, {
    'IntegerProperty': partial(_v, lambda v: int(v)),
    'FloatProperty': partial(_v, lambda v: float(v)),
    'BooleanProperty': partial(_v, lambda v: v == 'true'),
    'DateProperty': partial(_v, lambda v: date.fromtimestamp(int(v) / 1000)),
    'DateTimeProperty': partial(_v, lambda v: datetime.fromtimestamp(int(v) / 1000)),
})

val_to_str = partial(_val, {
    'BooleanProperty': partial(_v, lambda v: 'true' if v else 'false'),
    'DateProperty': partial(_v, lambda v: int(time.mktime(v.timetuple())) * 1000),
    'DateTimeProperty': partial(_v, lambda v: int(time.mktime(v.timetuple())) * 1000),
})


class Resource(object):
    model = None

    class InvalidFilter(Exception):
        pass

    class InvalidValue(Exception):
        pass

    def __init__(self, instance):
        self.instance = instance

    def __iter__(self):
        for property_name in self.get_model_properties():
            yield property_name

    @classmethod
    def get_model_properties(cls):
        properties = cls.model._properties
        ret = {}

        for prop_name, prop_type in properties.items():
            ret[prop_name] = prop_type.__class__.__name__.replace('Property', '').lower()
        return ret

    def as_dict(self, include_class_info=True):
        ret = {}

        for prop in self:
            ret[prop] = val_to_str(self.model._properties[prop],
                                   getattr(self.instance, prop))

        ret['id'] = self.instance.key.id()

        if include_class_info:
            ret['class'] = self.instance.__class__.__name__

        return ret

    @classmethod
    def get(cls, id):
        try:
            id = int(id)
        except ValueError:
            pass

        instance = cls.model.get_by_id(id)

        if instance is not None:
            return cls(instance).as_dict()

        return None

    @classmethod
    def list(cls, query=None):
        def _list(query):
            if query is None:
                query = cls.model.query()

            for row in query:
                yield cls(row)

        rows = [row.as_dict(include_class_info=False) for row in _list(query)]

        return {
            'objects': rows,
            'class': cls.model.__class__.__name__,
            'count': len(rows)
        }

    @classmethod
    def query(cls, **filters):
        query = cls.model.query()

        for prop, val in filters.items():
            prop = cls.model._properties[prop]

            try:
                query = query.filter(prop == val_from_str(prop, val))
            except (BadFilterError, ValueError), e:
                raise cls.InvalidFilter(unicode(e))

        return cls.list(query=query)

    @classmethod
    def update(cls, id, values):
        try:
            id = int(id)
        except ValueError:
            pass

        instance = cls.model.get_by_id(id)

        if instance is not None:
            for attr, val in values.items():
                try:
                    setattr(instance, attr, val)
                except BadValueError, e:
                    raise cls.InvalidValue(e)

            instance.put()
            return cls(instance).as_dict()

        return None

    @classmethod
    def create(cls, values):
        instance = cls.model(**values)
        instance.put()
        return cls(instance).as_dict()

    @classmethod
    def delete(cls, id):
        try:
            id = int(id)
        except ValueError:
            pass

        instance = cls.model.get_by_id(id)

        if instance is not None:
            instance.key.delete()
            return True

        return False

    @classmethod
    def describe(cls):
        return {
            'model': cls.model.__name__,
            'fields': cls.get_model_properties(),
        }


def resource_for_model(model):
    return type('%sResource' % model.__name__,
                (Resource,),
                {'model': model})
