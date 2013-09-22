from register import register
from discovery import discover_models
from resource import resource_for_model
from views import BaseResourceHandler

import config


__all__ = ['routes']


class _LazyRoutes(object):
    def __iter__(self):
        for cls, handler in register:
            for r in self._build_routes(cls, handler):
                yield r

    def _build_routes(self, cls, handler):
        if handler is None:
            handler = self._handler_for_class(cls)

        return [r for r in handler.routes()]

    @staticmethod
    def _handler_for_class(cls):
        return type('%sResourceHandler' % cls.__name__,
                    (BaseResourceHandler,),
                    {'resource_class': resource_for_model(cls)})

if hasattr(config, 'RESOURCES_AUTODISCOVER'):
    discover_models(config.RESOURCES_AUTODISCOVER)

routes = _LazyRoutes()
