import json
import webapp2


class BaseResourceHandler(webapp2.RequestHandler):
    resource_class = None

    def get(self, *args, **kwargs):
        action = 'list'

        if len(args) != 0:
            if args[0] == 'describe':
                action = 'describe'
            elif args[0] != '':
                action = 'get'

        if action == 'describe':
            ret = self.resource_class.describe()
        elif action == 'get':
            ret = self.resource_class.get(args[0])
            if ret is None:
                self.response.set_status(404)
                return
        else:
            if self.request.arguments():
                filter = dict((a, self.request.get(a)) for a in self.request.arguments())
                ordering = None

                if '_o' in filter:
                    ordering = filter['_o'].split(',')
                    del filter['_o']

                try:
                    ret = self.resource_class.query(ordering=ordering, **filter)
                except (self.resource_class.InvalidFilter, self.resource_class.InvalidOrderingProperty), e:
                    self.response.set_status(400)
                    self.response.write(unicode(e))
                    return
            else:
                ret = self.resource_class.list()

        self.response.write(json.dumps(ret))

    def post(self, *args, **kwargs):
        if len(args) == 0 or args[0] == '':
            self.response.set_status(400)
            return

        id = args[0]

        try:
            data = json.loads(self.request.body)
        except ValueError, e:
            self.response.set_status(400)
            self.response.write(unicode(e))
            return

        try:
            if id is not None:
                ret = self.resource_class.update(id, data)
            else:
                ret = self.resource_class.create(data)
        except self.resource_class.InvalidValue, e:
            self.response.set_status(400)
            self.response.write(unicode(e))
            return

        self.response.write(json.dumps(ret))

    def delete(self, *args, **kwargs):
        if not len(args) or args[0] == '':
            self.response.set_status(400)
            return

        if not self.resource_class.delete(args[0]):
            self.response.set_status(404)

        return

    @classmethod
    def routes(cls):
        return (
            ('/%s' % cls.resource_class.model.__name__.lower(), cls),
            ('/%s/([^\/]*)\/?' % cls.resource_class.model.__name__.lower(), cls),
        )

