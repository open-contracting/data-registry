Command-line interface
======================

.. code-block:: bash

   ./manage.py --help

Commands
--------

manageprocess
~~~~~~~~~~~~~

Orchestrate and evaluate all jobs and tasks.

.. code-block:: bash

   ./manage.py manageprocess

.. _cli-workers:

Workers
-------

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
