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

The default values in the ``settings.py`` file should be appropriate as-is. You can override them by setting :ref:`environment-variables`.

Backend
~~~~~~~

-  Run the server, replacing ``USERNAME`` AND ``PASSWORD``:

   .. code-block:: bash

      env SCRAPYD_URL=https://USERNAME:PASSWORD@collect.kingfisher.open-contracting.org ./manage.py runserver

   .. note::

      To test integration with the production version of Spoonbill, you also need to set the ``SPOONBILL_API_USERNAME`` and ``SPOONBILL_API_PASSWORD`` environment variables.

.. _django-shell:

-  Open a Django shell:

   .. code-block:: bash

      ./manage.py shell

   When using Docker:

   .. code-block:: bash

      docker compose run -e LOG_LEVEL=DEBUG --rm web python manage.py shell

-  Run tests:

   .. code-block:: bash

      ./manage.py test

Implementation notes
^^^^^^^^^^^^^^^^^^^^

-  As much as possible, use a single entrypoint (API) to other applications to limit coupling.
-  This project uses `Django signals <https://docs.djangoproject.com/en/4.2/topics/signals/>`__ (`reference <https://docs.djangoproject.com/en/4.2/ref/signals/>`__), which makes the code harder to understand, but guarantees that our desired actions are performed, regardless of how the related operation was called (for example, whether from a model, queryset or cascade).
-  The `update_fields <https://docs.djangoproject.com/en/4.2/ref/models/instances/#ref-models-update-fields>`__ argument must include any ``auto_now`` fields.

Frontend
~~~~~~~~

Autobuild the stylesheets
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   npx webpack --watch

Update the flags
^^^^^^^^^^^^^^^^

`Hampus Joakim Borgos <https://github.com/hampusborgos/country-flags>`__ maintains more accurate flags than `Lipis <https://github.com/lipis/flag-icons>`__.

.. code-block:: bash

   curl -LO https://github.com/hampusborgos/country-flags/archive/refs/heads/main.zip
   unzip main.zip
   rm -rf data_registry/static/img/flags/
   mv country-flags-main/ data_registry/static/img/flags
   rm -rf country-flags-main/ main.zip

Translate with Transifex
^^^^^^^^^^^^^^^^^^^^^^^^

See how to `update Django translations <https://ocp-software-handbook.readthedocs.io/en/latest/python/i18n.html>`__ and use `Transifex <https://www.transifex.com/open-contracting-partnership-1/data-registry/>`__.
