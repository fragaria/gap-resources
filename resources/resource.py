from google.appengine.ext import ndb
from google.appengine.api.datastore_errors import BadFilterError, BadValueError, BadRequestError

from serialization import val_from_str, val_to_str


__all__ = ['Resource', 'resource_for_model']


class Resource(object):
    model = None
    default_ordering = None
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

    @classmethod
    def _propertize_vals(cls, values):
        propertized = {}
        for prop_name, val in values.items():
            # Skip values which are not in model.
            if prop_name in cls.model._properties:
                prop = cls.model._properties[prop_name]
                if isinstance(prop, ndb.ComputedProperty):
                    continue
                try:
                    if prop._repeated:
                        propertized[prop_name] = [val_from_str(prop, item) for item in val]
                    else:
                        propertized[prop_name] = val_from_str(prop, val)

                except ValueError, e:
                    raise cls.InvalidValue(e)
        return propertized

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
                    ResourceClass = register.get_handler(related.__class__).resource_class
                    ret[prop] = ResourceClass(related).as_dict(include_class_info=include_class_info)
                    continue

            if self.instance._properties[prop]._repeated:
                ret[prop] = [val_to_str(p, v) for v in getattr(self.instance, prop)]
            else:
                ret[prop] = val_to_str(p, getattr(self.instance, prop))

        ret['id'] = self.instance.key.id() if self.instance.key is not None else None

        if include_class_info:
            ret['model'] = self.instance.__class__.__name__
        if hasattr(self.instance, 'export_resource'):
            ret = self.instance.export_resource(ret)

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
    def queryset(cls):
        return cls.model.query()

    @classmethod
    def __parse_ordering(cls, ordering):
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

        return orderings

    @classmethod
    def list(cls, ordering=None, query=None, span_keys=None):
        def _list(ordering, query):
            if query is None:
                query = cls.queryset()

            orderings = cls.default_ordering

            if ordering is not None:
                orderings = cls.__parse_ordering(ordering)

            if orderings is not None:
                query = query.order(*orderings)

            for row in query:
                yield cls(row)

        rows = [row.as_dict(include_class_info=False, span_keys=span_keys)
                for row in _list(ordering, query)]

        return rows

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
            propertized = cls._propertize_vals(values)

            try:
                cls._update_properties(instance, propertized)
            except BadValueError, e:
                raise cls.InvalidValue(e)

            instance.put()
            return cls(instance).as_dict(span_keys=span_keys)

        return None

    @classmethod
    def _update_properties(cls, instance, values):
        instance.populate(**values)

    @classmethod
    def create(cls, values, span_keys=None):
        propertized = cls._propertize_vals(values)
        instance = cls.model()
        cls._update_properties(instance, propertized)
        instance.put()
        return cls(instance).as_dict(span_keys=span_keys)

    @classmethod
    def delete(cls, id, *args, **kwargs):
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
    def describe(cls, *args, **kwargs):
        fields = {}

        for prop_name, prop_type in cls._model_props().items():
            prop = cls.model._properties[prop_name]
            info = {
                'type': prop_type,
                'verbose_name': prop._verbose_name or prop_name,
                'required': prop._required,
                'indexed': prop._indexed,
                'repeated': prop._repeated,
            }

            if prop._default:
                info['default'] = prop._default

            if prop._choices:
                info['choices'] = list(prop._choices)

            if prop._validator:
                info['validator'] = prop._validator

            fields[prop_name] = info

        return {
            'model': cls.model.__name__,
            'fields': fields,
        }


def resource_for_model(model):
    return type('%sResource' % model.__name__, (Resource,), {'model': model})
