System administrators
=====================

.. admonition:: One-time setup

   -  `Create a .netrc file <https://ocdsdeploy.readthedocs.io/en/latest/use/http.html#netrc>`__ to authenticate the ``collect`` login on the ``collect.data.open-contracting.org`` machine.
   -  `Create a ~/.config/scrapy.cfg file <https://kingfisher-collect.readthedocs.io/en/latest/scrapyd.html#configure-kingfisher-collect>`__ with:

      .. code-block:: ini

         [deploy:registry]
         url = https://collect.data.open-contracting.org/
         project = kingfisher

.. _admin-update-apps:

Deploy applications
-------------------

If the Salt configuration has changed, `deploy the service <https://ocdsdeploy.readthedocs.io/en/latest/deploy/deploy.html>`__:

.. code-block:: bash

   ./run.py --state-output=changes 'registry' state.apply

Kingfisher Collect
~~~~~~~~~~~~~~~~~~

#. If the ``requirements.txt`` file has changed, deploy the service as above.
#. `Deploy the latest version to Scrapyd <https://ocdsdeploy.readthedocs.io/en/latest/use/kingfisher-collect.html#update-spiders-in-kingfisher-collect>`__. If your local repository is up-to-date:

   .. code-block:: bash

      scrapyd-deploy registry

Kingfisher Process, Pelican backend, Pelican frontend, Data Registry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

For Scrapyd, the  ``scrapy_log`` key in the job's ``context`` links to the crawl log. For example, run, from the server, replacing ``JOB_ID``:

.. code-block::  bash

   curl http://localhost:6800/logs/kingfisher/kyrgyzstan/JOB_ID.log

.. _admin-wipe:

Delete a job
~~~~~~~~~~~~

A job can stall (always "running"). The only solution is to delete it.

#. If you expect the job to stall again, :ref:`freeze the publication<admin-unpublish-freeze>`.
#. `Find the job <https://data.open-contracting.org/admin/data_registry/job/>`__ in the Django admin.
#. Delete the job. This also cancels the Kingfisher Collect crawl in Scrapyd.

The Kingfisher Process, Pelican, Exporter and Flattener tasks use RabbitMQ. In exceptional circumstances, it might be desirable to purge relevant queues in its `management interface <https://ocdsdeploy.readthedocs.io/en/latest/use/rabbitmq.html#access-the-management-interface>`__.

.. warning::

   Purging queues affects all running jobs! It is not possible to purge only one job's messages from a queue.

Restart a task
~~~~~~~~~~~~~~

If it's a small publication, :ref:`delete the job<admin-wipe>`, instead. The :ref:`cli-manageprocess` command will create a new job.

Kingfisher Collect
  Delete the job, instead.
Kingfisher Process
  Delete the job, instead.

  Kingfisher Process is started by Kingfisher Collect, not by this project; replicating the integration is out of scope for this guide. To debug, download the data and run Process' ``load`` `command <https://kingfisher-process.readthedocs.io/en/latest/cli.html#load>`__.
Pelican
  Delete the dataset, using Pelican backend's ``remove`` `command <https://pelican-backend.readthedocs.io/en/latest/tasks/datasets.html#remove>`__.

  Change the status of the Pelican task and subsequent tasks to ``PLANNED``, then change the status of the job to ``RUNNING``.
Exporter
  The worker will delete all the files in the job directory within the ``EXPORTER_DIR`` :ref:`directory<env-exporter-flattener>`.

  Publish a message from the :ref:`Django shell<django-shell>`, using the compiled collection in Kingfisher Process:

  .. code-block:: bash

     from exporter.util import publish

     publish({"job_id": 123, "collection_id": 456}, "exporter_init")
Flattener
  Delete the ``.csv.tar.gz`` or ``.xlsx`` files in the job directory within the ``EXPORTER_DIR`` :ref:`directory<env-exporter-flattener>`.

  Publish a message from the :ref:`Django shell<django-shell>`:

  .. code-block:: bash

     from exporter.util import publish

     publish({"job_id": 123}, "flattener_init")
