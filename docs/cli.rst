Command-line interface
======================

.. code-block:: bash

   ./manage.py --help

Commands
--------

.. _cli-manageprocess:

manageprocess
~~~~~~~~~~~~~

Orchestrate and evaluate all jobs and tasks.

This calls :func:`data_registry.process_manager.process` with each publication.

.. code-block:: bash

   ./manage.py manageprocess

.. _cli-workers:

Workers
-------

.. note::

   `Consumers declare and bind queues, not publishers <https://ocp-software-handbook.readthedocs.io/en/latest/services/rabbitmq.html#bindings>`__.

   Start each worker before publishing messages with the :ref:`cli-manageprocess` command.

.. tip::

   Set the ``LOG_LEVEL`` environment variable to ``DEBUG`` to see log messages about message processing. For example:

   .. code-block:: bash

      env LOG_LEVEL=DEBUG ./manage.py flattener

exporter
~~~~~~~~

Export JSON files from compiled collections in Kingfisher Process.

.. code-block:: bash

   ./manage.py exporter

flattener
~~~~~~~~~

Convert JSON files to CSV and Excel files.

.. code-block:: bash

   ./manage.py flattener

wiper
~~~~~

Delete the files exported from compiled collections in Kingfisher Process.

.. code-block:: bash

   ./manage.py wiper
