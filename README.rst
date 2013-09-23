gap-resources
=============

Installation
------------

1. Install the package by::

    bin/gap install -e 'git+https://github.com/fragaria/gap-resources'


2. Add routes to src/routes.py::

    routes = (
        ...
        include('/_my_resources_base_url', 'lib/resources')
        ...
    )

3. Register your models in src/routes.py::

    from myapp.models import MyModel
    from resources import register
    register(MyModel)

4. Register models for whole package

Open src/config.py in your project and add RESOURCES_AUTODISCOVER with list of modules where resources should look for models.

Example:::

        RESOURCES_AUTODISCOVER = [
            'app.myapp.models',
        ]

5. Start your app and list your project on

    http://localhost:8080/_my_resources_base_url/

List of interfaces
==================

``GET .``
    list of models
``GET <model-slug>/``
    model objects list
``GET <model-slug>/describe``
    full description
``POST <model-slug>/<id>``
    updates existing object (and returns its data)
``POST <model-slug>/``
    creates new object (and returns it)

see `resources/views.py <resources/views.py>`_ for details

