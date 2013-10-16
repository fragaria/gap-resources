import re
import json
import webapp2

from google.appengine.api import namespace_manager, users
from google.appengine.ext.db import metadata
from google.appengine.ext.ndb import stats
from google.appengine.ext import db
from gap.utils.decorators import as_view

from namespace import NamespaceModel



def slugify(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()


class BaseResourceHandler(webapp2.RequestHandler):
    resource_class = None

    def _keys_to_span(self):
        if '_s' in self.request.arguments():
            return self.request.get('_s').split(',')

        return None

    def _res(self, method, *args, **kwargs):
        kwargs['span_keys'] = self._keys_to_span()
        return getattr(self.resource_class, method)(*args, **kwargs)

    def dispatch(self):
        res = super(BaseResourceHandler, self).dispatch()
        self.response.headers['Content-Type'] = 'application/json'
        return res

    def describe(self):
        self.response.write(json.dumps(self._res('describe')))

    def options(self, id=None):
        return

    def get(self, id=None):
        action = 'list'

        if id is not None and id != '':
            action = 'get'

        if action == 'get':
            ret = self._res('get', id)
            if ret is None:
                self.abort(404)
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

    def post(self, id=None):
        if id == '':
            id = None
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

    def delete(self, id=None):
        if id is None:
            self.response.set_status(400)
            return

        if not self._res('delete', id):
            self.response.set_status(404)

        return

    @classmethod
    def slugify(cls):
        '''converts CamelCase to camel-case'''
        return slugify(cls.resource_class.model.__name__)

    @classmethod
    def uri_for(cls, request):
        return webapp2.uri_for('model-resource-root-%s' % cls.slugify(), None, '')

    @classmethod
    def routes(cls):
        slugified = cls.slugify()
        return (
            webapp2.Route(r'/%s/describe' % slugified, cls, name='model-resource-describe-%s' % slugified, handler_method='describe'),
            webapp2.Route(r'/%s/<id:[^/]*><:/?>' % slugified, cls, name='model-resource-%s' % slugified),
            webapp2.Route(r'/%s<:/?>' % slugified, cls, name='model-resource-root-%s' % slugified),
        )


class NamespaceHandler(BaseResourceHandler):

    def _exists_namespace(self, name):
        existing_namespaces = metadata.get_namespaces()
        return name in existing_namespaces

    def get(self, *args, **kwargs):
        namespace = None
        action = 'list'

        if len(args) != 0:
            if len(args) >= 2:
                namespace = args[0]
                action = args[1]
            else:
                action = args[0]

            if action not in ['describe', 'query', 'get', 'list']:
                self.abort(500, 'Unknown action %s' % action)

        if namespace is None:  # namespace '' is the default namespace
            if action == 'describe':
                ret = 'Namespace API provides actions: get, list, query (with name parameter)'
            elif action == 'query':
                arguments = self.request.arguments()
                namespace = self.request.get('name')
                if not namespace:
                    self.response.set_status(500)
                else:
                    if not self._exists_namespace(namespace):
                        self.response.set_status(404)
                return
            elif action == 'get':
                ret = namespace_manager.get_namespace()
            else:  # list
                ret = metadata.get_namespaces()
                ret.sort()
        else:
            if not self._exists_namespace(namespace):
                self.abort(404, 'Namespace %s does not exist' % namespace)
                return
            if action == 'describe':  # namespace statistics
                namespace_stat = stats.NamespaceGlobalStat.query().get()
                ret = {
                    'bytes': namespace_stat.bytes if namespace_stat else 0,
                    'count': namespace_stat.count if namespace_stat else 0,
                    'timestamp': namespace_stat.timestamp if namespace_stat else 0
                }
            elif action == 'query':
                # no idea what belongs here
                return
            elif action == 'get':
                # no idea what belongs here
                return
            else:  # list
                current_namespace = namespace_manager.get_namespace()
                namespace_manager.set_namespace(namespace)
                ret = metadata.get_kinds()
                namespace_manager.set_namespace(current_namespace)

        self.response.write(json.dumps(ret))

    def post(self, *args, **kwargs):
        #TODO block post requests?
        if len(args) < 2 or not args[0] or not args[1]:
            self.response.set_status(400)
            return

        if args[0] == 'create':
            action = 'create'
        elif args[0] == 'set':
            action = 'set'
        else:
            self.response.set_status(400)
            return

        try:
            namespace_data = json.loads(self.request.body)
        except ValueError, e:
            self.response.set_status(400)
            self.response.write(unicode(e))
            return

        # set and create namespace
        try:
            namespace_name = namespace_data['name']
            if action == 'set':
                namespace = NamespaceModel.query(NamespaceModel.name == namespace_name).get()
                if not namespace:
                    self.response.set_status(404)
                namespace_manager.set_namespace(namespace_name)
                ret = ''
            elif action == 'create':
                namespace = NamespaceModel.query(NamespaceModel.name == namespace_name).get()
                if namespace:
                    self.response.set_status(500)  # already exists

                if not namespace_manager.validate_namespace(namespace_name):
                    self.response.set_status(500)  # invalid name

                if not users.is_current_user_admin():
                    self.response.set_status(500)  # only admin can add new namespace

                current_namespace = namespace_manager.get_namespace()
                namespace_manager.set_namespace(namespace_name)

                NamespaceModel.create(name=namespace_name, description=namespace_data['description'])

                namespace_manager.set_namespace(current_namespace)
                ret = ''
            else:
                self.response.set_status(500)
                ret = None
        except self.resource_class.InvalidValue, e:
            self.response.set_status(400)
            self.response.write(unicode(e))
            return

        self.response.write(json.dumps(ret))

    def delete(self, *args, **kwargs):
        self.abort(500, 'Action not supported')
        # if not len(args) or args[0] == '':
        #     self.response.set_status(400)
        #     return
        #
        # namespace = args[0]
        # existing_namespaces = metadata.get_namespaces()
        # if namespace not in existing_namespaces:
        #     self.response.set_status(404)
        #     return

    @classmethod
    def routes(cls):
        return (
            ('/namespace', cls),
            ('/namespace/([^\/\?]*)', cls),
            ('/namespace/([^\/]*)/([^\/\?]*)', cls)
        )

@as_view
def model_list(request, response):
    from resources import register
    response.write(json.dumps([
        {
            'model': model_class.__name__,
            'full_module': '%s.%s' % (model_class.__module__, model_class.__name__),
            'resource': handler.uri_for(request),
        } for model_class, handler in register
    ]))
