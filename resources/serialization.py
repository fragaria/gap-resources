from datetime import date, datetime
from functools import partial
import time

from google.appengine.ext import ndb


def _v(if_not_none_func, v, prop):
    if v is None:
        return None
    return if_not_none_func(v, prop)


def _val(map, prop, val):
    propname = prop.__class__.__name__
    return map[propname](val, prop) if propname in map else val


def _structured_prop_to_str(v, p):
    from resources import register

    ret = []
    cls = p._modelclass

    if not register.is_registered(cls):
        raise ValueError('Cannot dump %r within structured property, not '
                         'registered in resources registry.' % cls)
    if v:
        ValueResourceClass = register.get_handler(cls).resource_class

        for v_ in v:
            ret.append(ValueResourceClass(v_).as_dict())
    return ret


def _structured_prop_from_str(v, p):
    from resources import register

    ret = []
    cls = p._modelclass

    if not register.is_registered(cls):
        raise ValueError('Cannot load %r within structured property, not '
                         'registered in resources registry.' % cls)

    if v:
        ValueResourceClass = register.get_handler(cls).resource_class

        for v_ in v:
            propertized = ValueResourceClass._propertize_vals(v_)
            ret.append(ValueResourceClass.model(**propertized))

    return ret

def _local_structured_prop_to_str(value, property_class):
    ret = {}
    for prop_name, prop_class in value._properties.items():
        ret[prop_name] = val_to_str(prop_class, getattr(value, prop_name))
    return ret

def _local_structured_prop_from_str(value, property_class):
    raise NotImplementedError('This feature is not finished yet. Needs testing!!')
    ret = {}
    for prop_name, prop_class in property_class._modelclass._properties.items():
        ret[prop_name] = str_to_val(prop_class, getattr(value, prop_name))
    return ret



val_from_str = partial(_val, {
    'IntegerProperty': partial(_v, lambda v, p: int(v)),
    'FloatProperty': partial(_v, lambda v, p: float(v)),
    'BooleanProperty': partial(_v, lambda v, p: v == 'true'),
    'DateProperty': partial(_v, lambda v, p: date.fromtimestamp(int(v) / 1000)),
    'DateTimeProperty': partial(_v, lambda v, p: datetime.fromtimestamp(int(v) / 1000)),
    'KeyProperty': partial(_v, lambda v, p: ndb.Key(v['model'], v['id'])),
    'StructuredProperty': partial(_v, _structured_prop_from_str),
})

val_to_str = partial(_val, {
    'BooleanProperty': partial(_v, lambda v, p: 'true' if v else 'false'),
    'DateProperty': partial(_v, lambda v, p: int(time.mktime(v.timetuple())) * 1000),
    'DateTimeProperty': partial(_v, lambda v, p: int(time.mktime(v.timetuple())) * 1000),
    'KeyProperty': partial(_v, lambda v, p: {'model': v.kind(), 'id': v.id()}),
    'StructuredProperty': partial(_v, _structured_prop_to_str),
    'LocalStructuredProperty': partial(_v, _local_structured_prop_to_str),
})
