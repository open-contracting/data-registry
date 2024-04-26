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

.. _cli-exporter:

exporter
~~~~~~~~

Export JSON files from compiled collections in Kingfisher Process.

.. code-block:: bash

   ./manage.py exporter

-  Deletes files in the export directory before processing.
-  Uses a lockfile to determine whether the processing of a *job* is in-progress.
-  Acknowledges the messages after creating the lockfile, but before exporting files.

The lockfile is not deleted if an unhandled exception occurs.

.. admonition:: System administrators

   Delete the lockfile, if attempting to finish a task after fixing the error that raised the exception.

.. _cli-flattener:

flattener
~~~~~~~~~

Convert JSON files to CSV and Excel files.

.. code-block:: bash

   ./manage.py flattener

-  *Does not* delete files in the export directory before processing.
-  Uses a lockfile to determine whether the processing of a *file* is in-progress.
-  Acknowledges the messages before the `Splitter pattern <https://ocp-software-handbook.readthedocs.io/en/latest/services/rabbitmq.html#acknowledgements>`__ and before converting files.

The lockfile is not deleted if an unhandled exception occurs.

.. admonition:: System administrators

   Delete the lockfile, if attempting to finish a task after fixing the error that raised the exception.

wiper
~~~~~

Delete export directories.

.. code-block:: bash

   ./manage.py wiper
