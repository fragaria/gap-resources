from gap.utils.routes import include

routes = (
    ('/', 'gap.views.welcome_screen'),
    include('/resources', 'resources.routes'),
    ('/.*', 'gap.views.not_found')
)
