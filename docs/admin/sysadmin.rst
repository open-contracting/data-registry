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

Kingfisher Process, Pelican, Data Registry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Wait for the Docker image to build in GitHub Actions.

   -  `Kingfisher Process <https://github.com/open-contracting/kingfisher-process/actions>`__
   -  `Pelican Backend <https://github.com/open-contracting/pelican-backend/actions>`__
   -  `Pelican Frontend <https://github.com/open-contracting/pelican-frontend/actions>`__
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

   :ref:`Troubleshooting for site administrators<siteadmin-troubleshoot>`

.. _admin-wipe:

Delete a job
~~~~~~~~~~~~

A job can stall (always "running"). The only options are to set its *Status* to *COMPLETED* or to delete it, using the `Django admin <https://data.open-contracting.org/admin/>`__. Deleting a job also cancels the Scrapyd job.

.. warning::

   Deleting a job whose last completed task is not ``exporter`` could delete a Kingfisher Process collection or Pelican dataset while work is still queued in RabbitMQ, which could cause 100,000s of errors to be reported to Sentry.

If you expect the job to stall again, :ref:`freeze the publication<siteadmin-unpublish-freeze>`.

The Kingfisher Process, Pelican, Exporter and Flattener tasks use RabbitMQ. In exceptional circumstances, it might be desirable to purge relevant queues in the `management interface <https://rabbitmq.data.open-contracting.org/>`__.

.. warning::

   Purging queues affects all running jobs! It is not possible to purge only one job's messages from a queue.

Restart a task
~~~~~~~~~~~~~~

If it's a small publication, :ref:`delete the job<admin-wipe>`, instead (see warnings above). The :ref:`cli-manageprocess` command will create a new job. If it's a large publication (see warnings above):

Kingfisher Collect
  Delete the job, instead.
Kingfisher Process
  Delete the job, instead.

  Kingfisher Process is started by Kingfisher Collect, not by this project; replicating the integration is out of scope for this guide. To debug, download the data and run Process' ``load`` `command <https://kingfisher-process.readthedocs.io/en/latest/cli.html#load>`__.
Pelican
  Delete the dataset, using Pelican backend's ``remove`` `command <https://pelican-backend.readthedocs.io/en/latest/tasks/datasets.html#remove>`__.

  Change the status of the Pelican task and subsequent tasks to ``PLANNED``, then change the status of the job to ``RUNNING``.
Exporter
  Publish a message from the :ref:`Django shell<django-shell>`, using the compiled collection in Kingfisher Process:

  .. code-block:: bash

     from exporter.util import publish

     publish({"job_id": 123, "collection_id": 456}, "exporter_init")
Flattener
  Delete the ``.csv.tar.gz`` or ``.xlsx`` files in the job's directory within the ``EXPORTER_DIR`` :ref:`directory<env-exporter-flattener>`.

  Publish a message from the :ref:`Django shell<django-shell>`:

  .. code-block:: bash

     from exporter.util import publish

     publish({"job_id": 123}, "flattener_init")

Reset other applications
~~~~~~~~~~~~~~~~~~~~~~~~

In an extreme scenario, the other applications can be reset:

#. Cancel all Scrapyd jobs
#. Stop their Docker containers
#. Purge all RabbitMQ queues
#. `Backup the exchange_rates table <https://ocdsdeploy.readthedocs.io/en/latest/deploy/data-support.html#pelican-backend>`__
#. Drop the PostgreSQL databases for Kingfisher Process and Pelican backend
#. Delete the ``/data/deploy/pelican-backend/files/`` directory
#. `Deploy the service <https://ocdsdeploy.readthedocs.io/en/latest/deploy/deploy.html>`__ to recreate the databases
#. Run the `Django migrations <https://ocdsdeploy.readthedocs.io/en/latest/deploy/data-support.html#docker-apps>`__
#. Populate the ``exchange_rates`` table

.. note::

   This will cause database ``id`` values in old job contexts to collide with those in new job contexts. This is okay, because we don't touch old Kingfisher Process and Pelican tasks.
