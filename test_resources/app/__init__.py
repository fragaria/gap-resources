import webapp2

from resources import register

from app.example_module.models import ExampleModel

from routes import routes

if not register.is_registered(ExampleModel):
    register(ExampleModel)

handler = webapp2.WSGIApplication(routes=routes, debug=True)

