from datetime import date, datetime
from functools import partial
import time

from google.appengine.ext import ndb
from google.appengine.api.datastore_errors import BadFilterError, BadValueError, BadRequestError


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
    'KeyProperty': partial(_v, lambda v: ndb.Key(v['model'], v['id']))
})

val_to_str = partial(_val, {
    'BooleanProperty': partial(_v, lambda v: 'true' if v else 'false'),
    'DateProperty': partial(_v, lambda v: int(time.mktime(v.timetuple())) * 1000),
    'DateTimeProperty': partial(_v, lambda v: int(time.mktime(v.timetuple())) * 1000),
    'KeyProperty': partial(_v, lambda v: {'model': v.kind(), 'id': v.id()})
})


class Resource(object):
    model = None
    _span_keys = None

    class InvalidFilter(Exception):
        pass

    class InvalidValue(Exception):
        pass

    class InvalidOrderingProperty(Exception):
        pass

    def __init__(self, instance):
        self.instance = instance

    def __iter__(self):
        for property_name in self._model_props():
            yield property_name

    @classmethod
    def _model_props(cls):
        properties = cls.model._properties
        ret = {}

        for prop_name, prop_type in properties.items():
            ret[prop_name] = prop_type.__class__.__name__.replace('Property', '').lower()
        return ret

    def as_dict(self, include_class_info=True, span_keys=None):
        from register import register

        ret = {}
        keys_to_span = span_keys or self._span_keys

        for prop in self:
            p = self.model._properties[prop]

            # If this property should be spanned try to.
            if keys_to_span and prop in keys_to_span and isinstance(p, ndb.KeyProperty):
                key = getattr(self.instance, prop)
                related = key.get()

                # Use custom resource class if registered, fallback to defaults
                # if not.
                if register.is_registered(related.__class__):
                    ResourceHandler = register.get(related.__class__)[1]

                    if ResourceHandler is not None:
                        ResourceClass = ResourceHandler.resource_class
                    else:
                        ResourceClass = resource_for_model(related.__class__)

                    ret[prop] = ResourceClass(related).as_dict(include_class_info=include_class_info)
                    continue

            ret[prop] = val_to_str(p, getattr(self.instance, prop))

        ret['id'] = self.instance.key.id()

        if include_class_info:
            ret['model'] = self.instance.__class__.__name__

        return ret

    @classmethod
    def get(cls, id, span_keys=None):
        try:
            id = int(id)
        except ValueError:
            pass

        try:
            instance = cls.model.get_by_id(id)
        except BadRequestError:
            instance = None

        if instance is not None:
            return cls(instance).as_dict(span_keys=span_keys)

        return None

    @classmethod
    def list(cls, ordering=None, query=None, span_keys=None):
        def _list(ordering, query):
            if query is None:
                query = cls.model.query()

            if ordering is not None:
                orderings = []
                props = cls.model._properties

                if not hasattr(ordering, '__iter__'):
                    ordering = [ordering]

                for o in ordering:
                    prop, neg = (o[1:], True) if o.startswith('-') else (o, False)

                    if not prop in props or not props[prop]._indexed:
                        raise cls.InvalidOrderingProperty("Trying to order %r "
                                                          "by unknown property "
                                                          "%r" % (cls.__name__, prop))

                    if neg:
                        orderings.append(-props[prop])
                    else:
                        orderings.append(props[prop])

                query = query.order(*orderings)

            for row in query:
                yield cls(row)

        rows = [row.as_dict(include_class_info=False, span_keys=span_keys)
                for row in _list(ordering, query)]

        return {
            'objects': rows,
            'model': cls.model.__name__,
            'count': len(rows)
        }

    @classmethod
    def query(cls, ordering=None, span_keys=None, **filters):
        query = cls.model.query()

        for prop, val in filters.items():
            try:
                prop = cls.model._properties[prop]
                query = query.filter(prop == val_from_str(prop, val))
            except (BadFilterError, ValueError, KeyError), e:
                raise cls.InvalidFilter(unicode(e))

        return cls.list(ordering=ordering, query=query, span_keys=span_keys)

    @classmethod
    def update(cls, id, values, span_keys=None):
        try:
            id = int(id)
        except ValueError:
            pass

        try:
            instance = cls.model.get_by_id(id)
        except BadRequestError:
            instance = None

        if instance is not None:
            for attr, val in values.items():
                try:
                    setattr(instance, attr, val)
                except BadValueError, e:
                    raise cls.InvalidValue(e)

            instance.put()
            return cls(instance).as_dict(span_keys=span_keys)

        return None

    @classmethod
    def create(cls, values, span_keys=None):
        instance = cls.model(**values)
        instance.put()
        return cls(instance).as_dict(span_keys=span_keys)

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
            'fields': cls._model_props(),
        }


def resource_for_model(model):
    return type('%sResource' % model.__name__, (Resource,), {'model': model})
