from resources import register
from models import ExampleModel

register.register(ExampleModel)

routes = (
    ('.*', 'app.example_module.views.module_welcome_screen'),
)
