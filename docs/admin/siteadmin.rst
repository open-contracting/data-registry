Site administrators
===================

Use the `Django admin <https://data.open-contracting.org/admin/>`__ to:

-  Add and edit publications

   .. note::

      Once a new publication is added, the :ref:`cli-manageprocess` command will collect its data, unless *Frozen* is checked.

-  Check the status of a job and its tasks

   .. note::

      The :ref:`cli-flattener` task was added in September 2022, so earlier jobs have a *Last completed task* of "exporter (4/5)".

-  Review log entries for other administrators' actions

Publications and jobs can be searched by publication country and publication title.

.. note::

   The search performs only case normalization. For example, "Montreal" will not match "Montréal" (with an accent).

Add a publication
-----------------

Refer to our `internal documentation <https://docs.google.com/document/d/12d61HXZaD3wBYN479ShfZmc0xW29fJvmGNhkyf4xUhg/edit>`__ (contains links to internal resources).

Review publications
-------------------

From time to time, use the filters in the right-hand sidebar to:

-  Review publications for out-of-date or missing information:

   -  Non-frozen publications that weren't recently reviewed (*By last reviewed*: More than a year ago)
   -  Publications without all English and Spanish translations (*By untranslated*: Yes)
   -  Publications without licenses (*By data license*: Empty)
   -  Non-frozen publications without quality summaries (*By quality summary [en]*: Empty)
   -  Non-frozen publications without other information (*By incomplete*: Yes), one or more of:

      -  Country flag
      -  Country (en)
      -  Retrieval frequency
      -  Source URL
      -  Language (en)
      -  Description (en)
      -  Data availability (en)

-  Review publications for visibility and processing:

   -  Unpublished publications (*By public*: No)
   -  Frozen publications (*By frozen*: Yes)
   -  Historical publications (*By retrieval frequency*: This dataset is no longer updated by the publisher)

Review jobs
-----------

From time to time, use the filters in the right-hand sidebar to:

-  Check for completed jobs whose temporary data has not been deleted
-  Check for running jobs that are old

   .. note::

      The *WAITING* status is not used.

.. _admin-troubleshoot:

Troubleshoot a job
------------------

A job's detail page:

-  Displays the status, result and note (e.g. error messages) for each task, in the *Job tasks* section.

   If a task's result is ``FAILED``, but :func:`~data_registry.process_manager.process` considers the failure to be :class:`temporary<data_registry.exceptions.RecoverableException>`, then the :ref:`cli-manageprocess` command retries the task until it succeeds or fails permanently. Read the *Note*, and judge whether the failure is permanent. If so, you can set the job's *Status* to *COMPLETED* to stop the retries. The :ref:`cli-manageprocess` command will then delete the job's temporary data. The next job will be scheduled according to the publication's retrieval status.

   .. attention::

      If you want it scheduled sooner, prioritize `#350 <https://github.com/open-contracting/data-registry/issues/350>`__.

-  Defines and displays metadata (*Context*) from its tasks, in the *Management* section

   Use the metadata to troubleshoot other applications. For example, to check the Scrapy log, replace the hostname and port in the ``scrapy_log`` value with ``collect.data.open-contracting.org``.

   .. seealso::

      How to check on progress in:

      -  `Kingfisher Process <https://ocdsdeploy.readthedocs.io/en/latest/use/kingfisher-process.html#check-on-progress>`__
      -  `Pelican <https://ocdsdeploy.readthedocs.io/en/latest/use/pelican.html#check-on-progress>`__

      This project's RabbitMQ management interface is at `rabbitmq.data.open-contracting.org <https://rabbitmq.data.open-contracting.org/>`__.

.. _admin-cancel:

Cancel a job
~~~~~~~~~~~~

A job can stall (always "running"). The only option is to `cancel <https://scrapyd.readthedocs.io/en/latest/api.html#cancel-json>`__ the Scrapyd job and set the job's *Status* to *COMPLETED* using the `Django admin <https://data.open-contracting.org/admin/>`__.

.. attention::

   To properly implement this feature, see `#352 <https://github.com/open-contracting/data-registry/issues/352>`__.

Restart a task
~~~~~~~~~~~~~~

You can restart the :ref:`Exporter<cli-exporter>` and :ref:`Flattener<cli-flattener>` tasks. Do this only if the ``data_registry_production_exporter_init`` and ``data_registry_production_flattener_init`` queues are empty in the `RabbitMQ management interface <https://rabbitmq.data.open-contracting.org/>`__.

.. note::

   The Flattener task publishes one message per file. You might receive a Sentry notification about a failed conversion, while other conversions are still enqueued or in-progress.

   The Exporter task publishes one message per job. This task *can* be restarted while the queue is non-empty – as long as another administrator has not restarted it independently.

#. `Access the job <https://data.open-contracting.org/admin/data_registry/job/>`__
#. Set only the *Exporter* and/or *Flattener* task's *Status* to *PLANNED*
#. Click *SAVE*

Any lockfiles are deleted to allow the task to run.

.. attention::

   See `#350 <https://github.com/open-contracting/data-registry/issues/350>`__.

Unpublish or freeze a publication
---------------------------------

#. `Find the publication <https://data.open-contracting.org/admin/data_registry/collection/>`__
#. Uncheck *Public*, to hide the publication
#. Check *Frozen*, to stop jobs from being scheduled
#. Click *Save* at the bottom of the page

Only *delete* a publication if it is a duplicate or if it was otherwise created in error.

Add an administrator
--------------------

#. Click *Add* next to *Users* in the left-hand menu
#. Fill in *Username* and *Password*, using a `strong password <https://www.lastpass.com/features/password-generator>`__
#. Click *Save and continue editing*

On the next form:

#. Fill in *First name*, *Last name* and *Email address*
#. Check *Staff status* (only James and Yohanna should have *Superuser status*)
#. Assign *Groups* (multiple can be selected, as they have non-overlapping permissions)

   Viewer
     Can view publications, quality issues, licenses, jobs and job tasks
   Contributor
     Can add/change publications, quality issues and licenses

#. Click *SAVE*

