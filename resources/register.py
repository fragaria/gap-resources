from app.resources.views import BaseResourceHandler


__all__ = ['register']


class ModelRegistry(object):
    class NotRegistered(Exception):
        pass

    def __init__(self):
        self._models = {}

    def __iter__(self):
        return iter(self._models.items())

    def __repr__(self):
        return '<ModelRegistry: %s>' % ','.join(self._models.values())

    def is_registered(self, cls):
        return cls in self._models

    def register(self, cls, handler=None):
        if handler is not None and not issubclass(handler, BaseResourceHandler):
            raise ValueError('Cannot register: %r must be subclass of '
                             'BaseResourceHandler.' % handler.__name__)
        self._models[cls] = handler

    def unregister(self, cls):
        if self.is_registered(cls):
            del self._models[cls]
        else:
            raise self.NotRegistered('Cannot unregister %r, not found in registry.' % cls.__name__)

    def models(self):
        return self._models.keys()


register = ModelRegistry()
