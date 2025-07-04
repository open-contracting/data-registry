Data Registry
=============

.. include:: ../README.rst

How it works
------------

This project is made up of two apps:

-  ``data_registry``: Serves the website, `metadata API <https://data.open-contracting.org/en/publications.json>`__ and admin site, and performs orchestration.
-  ``exporter``: Creates the bulk downloads in JSON, Excel and CSV format.

The complex part of the project is the orchestration. The tasks to orchestrate are:

-  Collect data, via `Scrapyd <https://scrapyd.readthedocs.io/en/latest/>`__, used as the `interface <https://kingfisher-collect.readthedocs.io/en/latest/scrapyd.html>`__ to `Kingfisher Collect <http://kingfisher-collect.readthedocs.io/en/latest/>`__
-  Pre-process data, via `Kingfisher Process <https://kingfisher-process.readthedocs.io/en/latest/>`__
-  Export JSON files, via the :ref:`cli-exporter` worker
-  Calculate coverage, via the :ref:`cli-coverage` worker, using `Cardinal <https://cardinal.readthedocs.io/en/latest/>`__
-  Export Excel and CSV files, via the :ref:`cli-flattener` worker, using `Flatterer <https://docs.flatterer.dev>`__

Each task is implemented as a :class:`~data_registry.process_manager.util.TaskManager` under the ``data_registry/process_manager/task`` directory. The ``JOB_TASKS_PLAN`` setting controls the order and choice of tasks.

The most relevant logic is:

-  the :ref:`cli-manageprocess` command, which calls...
-  the :func:`data_registry.process_manager.process` function with each publication, which calls...
-  the :meth:`data_registry.models.Collection.is_out_of_date` method to decide whether to start a job.

Word choice
-----------

"collection” has a different meaning in this project's code than in Kingfisher Collect or Kingfisher Process. It should be “publication”, as used in the UI and documentation.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   admin/index
   cli
   reference/index
   contributing/index
   api/index
