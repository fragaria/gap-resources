INSTALLATION
============

In your gap project ...

Install
-------

.. code:: python

    bin/gap install -e 'git+https://github.com/fragaria/gap-resources'

Add routes to src/routes.py
---------------------------

.. code:: python

    routes = (
        ...
        include('/_my_resources_base_url', 'lib/resources')
        ...
    )

Register your models in src/routes.py
-------------------------------------


.. code:: python

    from myapp.models import MyModel
    from resources import register
    register(MyModel)

Register models for whole package
---------------------------------
    
Open src/config.py and add RESOURCES_AUTODISCOVER with list of modules where resources should look for models.
    
Example:

.. code:: python

    RESOURCES_AUTODISCOVER = [
        'app.myapp.models',
    ]

Start your app and list your project on
---------------------------------------
    http://localhost:8080/_my_resources_base_url/mymodel

other urls are (relative to _my_resources_base_url)

:GET .: list of models
:GET ./<model-slug>/: model objects list
:GET ./<model-slug>/describe: full description
:POST ./<model-slug>/<id>: updates existing object (and returns its data)
:POST ./<model-slug>/: creates new object (and returns it)

