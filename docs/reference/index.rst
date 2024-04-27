Reference
=========

.. _environment-variables:

Environment variables
---------------------

See `OCP's approach to Django settings <https://ocp-software-handbook.readthedocs.io/en/latest/python/django.html#settings>`__. New variables are:

LOG_LEVEL
  The log level of the root logger

Collect task
~~~~~~~~~~~~

This project communicates with Kingfisher Collect via Scrapyd. However, Scrapyd has no endpoint for deleting data, so ``KINGFISHER_COLLECT_FILES_STORE`` is needed.

SCRAPYD_URL
  The base URL of Scrapyd, for example: ``http://localhost:6800``
SCRAPYD_PROJECT
  The project within Scrapyd
KINGFISHER_COLLECT_FILES_STORE
  The directory from which to **delete** the files written by Kingfisher Collect. If Kingfisher Collect and Kingfisher Process share a filesystem, this will be the same value for both services.

Process task
~~~~~~~~~~~~

This project communicates with Kingfisher Process via its `API <https://kingfisher-process.readthedocs.io/en/latest/reference/index.html#api>`__.

KINGFISHER_PROCESS_URL
  The base URL of Kingfisher Process

Pelican task
~~~~~~~~~~~~

This project communicates with Pelican frontend via its `API <https://pelican-frontend.readthedocs.io/en/latest/reference/index.html#api>`__.

PELICAN_FRONTEND_URL
  The base URL of Pelican frontend

.. _env-exporter-flattener:

Exporter and Flattener tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:ref:`cli-exporter` reads compiled releases directly from Kingfisher Process' database (like `Pelican backend <https://pelican-backend.readthedocs.io/en/latest/reference/workers.html#extract-kingfisher-process>`__).

RABBIT_URL
  The `connection string <https://pika.readthedocs.io/en/stable/examples/using_urlparameters.html#using-urlparameters>`__ for RabbitMQ
RABBIT_EXCHANGE_NAME
  The name of the RabbitMQ exchange. Follow the pattern ``kingfisher_process_{service}_{environment}`` like ``kingfisher_process_data_registry_production``
KINGFISHER_PROCESS_DATABASE_URL
  The `connection string <https://github.com/kennethreitz/dj-database-url#url-schema>`__ for Kingfisher Process's database
EXPORTER_DIR
  The directory to which the ``exporter`` app writes files

Spoonbill integration
~~~~~~~~~~~~~~~~~~~~~

SPOONBILL_URL
  The base URL of Spoonbill
SPOONBILL_API_USERNAME
  The username for `basic HTTP authentication <https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication#basic_authentication_scheme>`__
SPOONBILL_API_PASSWORD
  The password for basic HTTP authentication
SPOONBILL_EXPORTER_DIR
  The directory to which the ``exporter`` app writes files, from Spoonbill's perspective. This is relevant if this project or Spoonbill is running in a container.
