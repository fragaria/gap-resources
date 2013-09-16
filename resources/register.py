from views import BaseResourceHandler


__all__ = ['register']


class ModelRegistry(object):
    class NotRegistered(Exception):
        pass

    def __init__(self):
        self._models = []

    def __iter__(self):
        return iter(self._models)

    def __repr__(self):
        return '<ModelRegistry: %s>' % ','.join([unicode(m) for m in self.models()])

    def is_registered(self, cls):
        return cls in self.models()

    def register(self, cls, handler=None):
        if handler is not None and not issubclass(handler, BaseResourceHandler):
            raise ValueError('Cannot register: %r must be subclass of '
                             'BaseResourceHandler.' % handler.__name__)
        self._models.append((cls, handler))

    def unregister(self, cls):
        if self.is_registered(cls):
            for m, h in self._models:
                if m == cls:
                    self._models.remove((m, h))
                    break
        else:
            raise self.NotRegistered('Cannot unregister %r, not found in registry.' % cls.__name__)

    def models(self):
        return [m[0] for m in self._models]

    def get(self, cls):
        for m, h in self._models:
            if cls == m:
                return m, h


register = ModelRegistry()
