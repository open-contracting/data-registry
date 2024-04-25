Contributing
============

.. seealso::

   `Django <https://ocp-software-handbook.readthedocs.io/en/latest/python/django.html>`__ in the Software Development Handbook

Setup
-----

#. Install PostgreSQL and RabbitMQ
#. Create a Python 3.11 virtual environment
#. Install development dependencies:

   .. code-block:: bash

      pip install pip-tools
      pip-sync requirements_dev.txt

#. Set up the git pre-commit hook:

   .. code-block:: bash

      pre-commit install

#. Create the database:

   .. code-block:: bash

      createdb data_registry

#. Run database migrations and create a superuser:

   .. code-block:: bash

      ./manage.py migrate
      ./manage.py createsuperuser

Development
-----------

The default values in the settings.py file should be appropriate as-is. You can override them by setting :ref:`environment-variables`.

Backend
~~~~~~~

As much as possible, use a single entrypoint (API) to other projects to limit coupling. See :ref:`environment-variables` for details.

Run the web server
^^^^^^^^^^^^^^^^^^

Replacing ``USERNAME`` AND ``PASSWORD``:

.. code:: bash

   env SCRAPYD_URL=https://USERNAME:PASSWORD@collect.kingfisher.open-contracting.org ./manage.py runserver

.. note::

   To test integration with the production version of Spoonbill, you also need to set the ``SPOONBILL_API_USERNAME`` and ``SPOONBILL_API_PASSWORD`` environment variables.

Start workers
^^^^^^^^^^^^^

See :ref:`cli-workers`.

.. tip::

   Set the ``LOG_LEVEL`` environment variable to ``DEBUG`` to see log messages about message processing. For example:

   .. code-block:: bash

      env LOG_LEVEL=DEBUG ./manage.py flattener

.. note::

   Remember: `Consumers declare and bind queues, not publishers <https://ocp-software-handbook.readthedocs.io/en/latest/services/rabbitmq.html#bindings>`__. Start each worker before publishing messages.

Run tests
^^^^^^^^^

.. code-block:: bash

   ./manage.py test

Publish a message
^^^^^^^^^^^^^^^^^

To manually start a task, run, for example:

.. code:: python

   import os

   from exporter.util import publish
   os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

   publish({"job_id": 123}, "flattener_init")

Frontend
~~~~~~~~

Autobuild the stylesheets
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: bash

   npx webpack --watch

Update the flags
^^^^^^^^^^^^^^^^

`Hampus Joakim Borgos <https://github.com/hampusborgos/country-flags>`__ maintains more accurate flags than `Lipis <https://github.com/lipis/flag-icons>`__.

.. code:: bash

   curl -LO https://github.com/hampusborgos/country-flags/archive/refs/heads/main.zip
   unzip main.zip
   rm -rf data_registry/static/img/flags/
   mv country-flags-main/ data_registry/static/img/flags
   rm -rf country-flags-main/ main.zip

Translate with Transifex
^^^^^^^^^^^^^^^^^^^^^^^^

See how to `update Django translations <https://ocp-software-handbook.readthedocs.io/en/latest/python/i18n.html>`__ and use `Transifex <https://www.transifex.com/open-contracting-partnership-1/data-registry/>`__.
