from resource import resource_for_model
from views import BaseResourceHandler
from resource import Resource


__all__ = ['register']


class ModelRegistry(object):
    class NotRegistered(Exception):
        pass

    class AlreadyRegistered(Exception):
        pass

    def __init__(self):
        self._models = []

    def __iter__(self):
        return ( (model, self.handler_for_model(model, handler)) for model, handler in self._models)

    def __repr__(self):
        return '<ModelRegistry: %s>' % ','.join([unicode(m.__name__) for m in self.models()])

    def __call__(self, *args, **kwargs):
        return self.register(*args, **kwargs)

    def is_registered(self, cls):
        return cls in self.models()

    def register(self, cls, handler_or_resource=None):
        if cls in [c for c, h in self._models]:
            raise self.AlreadyRegistered('Cannot register %r, already present in registry.' % cls.__name__)

        handler = None

        if handler_or_resource is not None:
            if issubclass(handler_or_resource, Resource):
                handler = self.handler_for_model(cls, resource_class=handler_or_resource)
            elif issubclass(handler_or_resource, BaseResourceHandler):
                handler = handler_or_resource
            else:
                raise ValueError('Cannot register: %r must be subclass of '
                                 'BaseResourceHandler or Resource.' % handler_or_resource.__name__)

        if handler is None:
            handler = self.handler_for_model(cls)

        self._models.append((cls, handler))

    def unregister(self, cls):
        if self.is_registered(cls):
            for m, h in self._models:
                if m == cls:
                    self._models.remove((m, h))
                    break
        else:
            raise self.NotRegistered('Cannot unregister %r, not found in registry.' % cls.__name__)

    @staticmethod
    def handler_for_model(cls, handler=None, resource_class=None):
        if handler is None:
            handler = type(
                '%sResourceHandler' % cls.__name__,
                (BaseResourceHandler,),
                {'resource_class': resource_class or resource_for_model(cls)}
            )
        return handler

    def models(self):
        return [m[0] for m in self._models]

    def get(self, cls):
        for m, h in self._models:
            if cls == m:
                return m, h

    def get_handler(self, cls):
        return self.handler_for_model(*self.get(cls))


register = ModelRegistry()
