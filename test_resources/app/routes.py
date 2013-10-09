from gap.utils.routes import include

routes = (
    include('/resources', 'resources.routes'),
    ('/.*', 'gap.views.not_found')
)
