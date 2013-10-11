from register import register
from discovery import discover_models
from views import BaseResourceHandler

try:
    import config
except ImportError:
    config = None


__all__ = ['routes']


class _LazyRoutes(object):
    def __init__(self, static_routes, register):
        self.static_routes = static_routes
        self.register = register

    def __iter__(self):
        for r in self.static_routes:
            yield r

        for cls, handler in self.register:
            for r in self._build_routes(cls, handler):
                yield r

    def _build_routes(self, cls, handler):
        return [r for r in handler.routes()]


if hasattr(config, 'RESOURCES_AUTODISCOVER'):
    discover_models(config.RESOURCES_AUTODISCOVER)

routes = _LazyRoutes((
    ('/', 'resources.views.model_list'),
), register)
