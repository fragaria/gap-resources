import re
import json
import webapp2

from gap.utils.decorators import as_view


class BaseResourceHandler(webapp2.RequestHandler):
    resource_class = None

    def _keys_to_span(self):
        if '_s' in self.request.arguments():
            return self.request.get('_s').split(',')

        return None

    def _res(self, method, *args, **kwargs):
        kwargs['span_keys'] = self._keys_to_span()
        return getattr(self.resource_class, method)(*args, **kwargs)

    def get(self, *args, **kwargs):
        action = 'list'

        if len(args) != 0:
            if args[0] == 'describe':
                action = 'describe'
            elif args[0] != '':
                action = 'get'

        if action == 'describe':
            ret = self._res('describe')
        elif action == 'get':
            ret = self._res('get', args[0])
            if ret is None:
                self.response.set_status(404)
                return
        else:
            if self.request.arguments():
                filter = dict((a, self.request.get(a)) for a in self.request.arguments() if a not in ('_o', '_s'))
                ordering = None

                if '_o' in self.request.arguments():
                    ordering = self.request.get('_o').split(',')

                try:
                    ret = self._res('query', ordering=ordering, **filter)
                except (self.resource_class.InvalidFilter, self.resource_class.InvalidOrderingProperty), e:
                    self.response.set_status(400)
                    self.response.write(unicode(e))
                    return
            else:
                ret = self._res('list')

        self.response.write(json.dumps(ret))

    def post(self, *args, **kwargs):
        if len(args) == 1 and args[0] == '':
            self.response.set_status(400)
            self.response.write('Wrong args!')
            return

        id = args[0] if len(args) > 0 else None

        try:
            data = json.loads(self.request.body)
        except ValueError, e:
            self.response.set_status(400)
            self.response.write(unicode(e))
            return

        try:
            if id is not None:
                ret = self._res('update', id, data)
            else:
                ret = self._res('create', data)
        except self.resource_class.InvalidValue, e:
            self.response.set_status(400)
            self.response.write(unicode(e))
            return

        self.response.write(json.dumps(ret))

    def delete(self, *args, **kwargs):
        if not len(args) or args[0] == '':
            self.response.set_status(400)
            return

        if not self._res('delete', args[0]):
            self.response.set_status(404)

        return

    @classmethod
    def slugify(cls):
        '''converts CamelCase to camel-case'''
        name = cls.resource_class.model.__name__
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()

    @classmethod
    def uri_for(cls, request):
        return webapp2.uri_for('model-resource-description-%s' % cls.slugify())

    @classmethod
    def routes(cls):
        return (
            webapp2.Route('/%s' % cls.slugify(), cls, name='model-resource-description-%s' % cls.slugify()),
            webapp2.Route('/%s/([^\/]*)\/?' % cls.slugify(), cls, name='model-resource-%s' % cls.resource_class.model.__name__.lower()),
        )


@as_view
def model_list(request, response):
    from resources import register
    response.write(json.dumps([
        {
            'model': model_class.__name__,
            'full_module': '%s.%s' % (model_class.__module__ ,model_class.__name__),
            'resource': handler.uri_for(request),
        } for model_class, handler in register
    ]))
