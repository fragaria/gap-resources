import webapp2

from resources import register

from app.example_module.models import ExampleModel

if not register.is_registered(ExampleModel):
    register(ExampleModel)

from routes import routes

handler = webapp2.WSGIApplication(routes=routes, debug=True)

