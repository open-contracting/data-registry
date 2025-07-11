System administrators
=====================

Setup
-----

-  `Create a .netrc file <https://ocdsdeploy.readthedocs.io/en/latest/use/http.html#netrc>`__ with a ``collect`` login and ``collect.data.open-contracting.org`` machine.
-  `Create a ~/.config/scrapy.cfg file <https://kingfisher-collect.readthedocs.io/en/latest/scrapyd.html#configure-kingfisher-collect>`__ with:

   .. code-block:: ini

      [deploy:registry]
      url = https://collect.data.open-contracting.org/
      project = kingfisher

Deploy
------

If the Salt configuration has changed, `deploy the service <https://ocdsdeploy.readthedocs.io/en/latest/deploy/deploy.html>`__.

Kingfisher Collect
~~~~~~~~~~~~~~~~~~

#. If the ``requirements.txt`` file has changed, `deploy the service <https://ocdsdeploy.readthedocs.io/en/latest/deploy/deploy.html>`__.
#. `Deploy the latest version to Scrapyd <https://ocdsdeploy.readthedocs.io/en/latest/use/kingfisher-collect.html#update-spiders-in-kingfisher-collect>`__. If your local repository is up-to-date:

   .. code-block:: bash

      scrapyd-deploy registry

.. attention::

   When the Scrapyd service restarts (for example, when the server restarts), the running Scrapyd jobs are lost, and therefore the Collect :class:`~data_registry.process_manager.util.TaskManager` won't be able to check the task's status. :ref:`Cancel the job<admin-cancel>` and reschedule it (`#350 <https://github.com/open-contracting/data-registry/issues/350>`__).

Kingfisher Process, Data Registry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Wait for the Docker image to build in GitHub Actions.

   -  `Kingfisher Process <https://github.com/open-contracting/kingfisher-process/actions>`__
   -  `Data Registry <https://github.com/open-contracting/data-registry/actions>`__

#. Connect to the server as the ``deployer`` user:
   
   .. code-block:: bash

      ssh -p 2223 deployer@ocp13.open-contracting.org

#. `Update the application <https://ocdsdeploy.readthedocs.io/en/latest/deploy/docker.html#update-applications>`__.

Troubleshoot
------------

Read log files
~~~~~~~~~~~~~~

All containers log to standard output, which can be `read as usual using Docker <https://ocdsdeploy.readthedocs.io/en/latest/maintain/docker.html#review-log-files>`__.

.. seealso::

   :ref:`Troubleshooting for site administrators<admin-troubleshoot>`

Debug another application
~~~~~~~~~~~~~~~~~~~~~~~~~

Kingfisher Collect
  `Use Kingfisher Collect locally <https://kingfisher-collect.readthedocs.io/en/latest/local.html>`__.
Kingfisher Process
  -  Download the data from crawl directory in the ``KINGFISHER_COLLECT_FILES_STORE`` directory.
  -  Run Kingfisher Process' ``load`` `command <https://kingfisher-process.readthedocs.io/en/latest/cli.html#load>`__.
Coverage
  -  Download the ``full.jsonl.gz`` file from the job's directory in the ``EXPORTER_DIR`` directory.
  -  Run the `ocdscardinal coverage <https://cardinal.readthedocs.io/en/latest/cli/coverage.html>`__ command locally.
Flattener
  -  Download the ``*.jsonl.gz`` files from the job's directory in the ``EXPORTER_DIR`` directory.
  -  Run the `flatterer <https://flatterer.opendata.coop>`__ command locally.

Reset other applications
~~~~~~~~~~~~~~~~~~~~~~~~

The Kingfisher Process, Exporter and Flattener tasks use RabbitMQ. In an extreme scenario, the relevant queues can be purged in the `RabbitMQ management interface <https://rabbitmq.data.open-contracting.org/>`__.

.. warning::

   Purging queues affects all running jobs! It is not possible to purge only one job's messages from a queue.

In an extreme scenario, the other applications can be reset:

#. Cancel all Scrapyd jobs
#. Stop their Docker containers
#. Purge all RabbitMQ queues
#. Drop the PostgreSQL databases for Kingfisher Process
#. `Deploy the service <https://ocdsdeploy.readthedocs.io/en/latest/deploy/deploy.html>`__ to recreate the databases
#. Run the `Django migrations <https://ocdsdeploy.readthedocs.io/en/latest/deploy/data-support.html#docker-apps>`__

.. note::

   This will cause database ``id`` values in old job contexts to collide with those in new job contexts. This is okay, because we don't touch old Kingfisher Process tasks.
