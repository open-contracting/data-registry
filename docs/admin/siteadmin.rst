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

-  Check for failed jobs, and :ref:`restart tasks<admin-restart>` as appropriate (*By failed*: Yes)
-  Check for completed jobs whose temporary data has not been deleted (*By temporary data deleted*: No, *By status*: COMPLETED)
-  Check for running jobs that are old (*By status*: RUNNING)

.. note::

   The *WAITING* status is not used.

.. _admin-troubleshoot:

Troubleshoot a job
------------------

A job's detail page:

-  Displays the status, result and note (e.g. error messages) for each task, in the *Job tasks* section.

   If a task's result is ``FAILED``, but :func:`~data_registry.process_manager.process` considers the failure to be :class:`temporary<data_registry.exceptions.RecoverableError>`, then the :ref:`cli-manageprocess` command retries the task until it succeeds or fails permanently. Read the *Note*, and judge whether the failure is permanent. If so, you can set the job's *Status* to *COMPLETED* to stop the retries. The :ref:`cli-manageprocess` command will then delete the job's temporary data. The next job will be scheduled according to the publication's retrieval status.

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

.. _admin-restart:

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

Unblock the Process task
~~~~~~~~~~~~~~~~~~~~~~~~

Bugs can cause a job to get stuck on the Process task. To diagnose and fix a bug, run Kingfisher Process' `collectionstatus <https://kingfisher-process.readthedocs.io/en/latest/cli.html#collectionstatus>`__ command and select the collection's notes, for example:

.. code-block:: sql

   SELECT * FROM collection_note WHERE collection_id = 100;

If the collection is large, you can manually unblock the Process task.

No data collected
^^^^^^^^^^^^^^^^^

.. note::

   This bug is fixed. The Process task fails with "Collection is empty".

If the ``collectionstatus`` command shows that no collection files were created and that the compiled collection has started but not ended:

.. code-block:: none
   :emphasize-lines: 5-6,10-13

   steps: compile
   data_type: to be determined
   store_end_at: 2001-02-03 04:05:06.979418
   completed_at: 2001-02-03 04:05:07.074971
   expected_files_count: 0
   collection_files: 0
   processing_steps: 0

   Compiled collection
   compilation_started: True
   store_end_at: None
   completed_at: None
   collection_files: 0
   processing_steps: 0
   completable: yes

Then, confirm that the Collect task didn't write files, by checking the crawl's log file in `Scrapyd <https://kingfisher-collect.readthedocs.io/en/latest/scrapyd.html#using-the-scrapyd-web-interface>`__ for a message like:

.. code-block:: none

   2001-02-03 04:05:06 [my_spider] INFO: +---------------- DATA DIRECTORY ----------------+
   2001-02-03 04:05:06 [my_spider] INFO: |                                                |
   2001-02-03 04:05:06 [my_spider] INFO: | Something went wrong. No data was downloaded.  |
   2001-02-03 04:05:06 [my_spider] INFO: |                                                |
   2001-02-03 04:05:06 [my_spider] INFO: +------------------------------------------------+

If so, run Kingfisher Process' `closecollection <https://kingfisher-process.readthedocs.io/en/latest/cli.html#closecollection>`__ command using the ID of the **original** collection, to allow the task to finish.

Processing step remaining
^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::

   This bug is fixed. It was diagnosed by observing one remaining load step and a note like:

   .. code-block:: none

      Empty format 'empty package' for file /data/my_spider/20010203_040506/E76/my_file.json (id: 55555).

   The fix was to delete load steps for empty packages.

If the output looks like:

.. code-block:: none
   :emphasize-lines: 4,7,9,11,15-17,20

   steps: compile
   data_type: release package
   store_end_at: 2001-02-03 04:05:06.979418
   completed_at: None
   expected_files_count: 654321
   collection_files: 654321
   processing_steps: 1
   2001-02-03 04:05:07,074 DEBUG [process.management.commands.compiler:120] Collection my_spider:2001-02-03 04:05:06 (id: 100) not compilable (load steps remaining)
   compilable: no (or not yet)
   2001-02-03 04:05:07,074 DEBUG [process.management.commands.finisher:130] Collection my_spider:2001-02-03 04:05:06 (id: 100) not completable (steps remaining)
   completable: no (or not yet)

   Compiled collection
   compilation_started: False
   store_end_at: None
   completed_at: None
   collection_files: 0
   processing_steps: 0
   2024-07-04 14:45:01,718 DEBUG [process.management.commands.finisher:114] Collection my_spider:2001-02-03 04:05:06 (id: 101) not completable (compile steps not created)
   completable: no (or not yet)

Then, confirm that the messages corresponding to the remaining processing steps have already been consumed by the `file_worker <https://kingfisher-process.readthedocs.io/en/latest/cli.html#file-worker>`__ worker, by checking `RabbitMQ's management interface <https://rabbitmq.data.open-contracting.org/>`__. If so, select the remaining load steps for the original collection, for example:

.. code-block:: sql

   SELECT collection_file_id FROM processing_step WHERE name = 'LOAD' AND collection_id = 100;

.. code-block:: none

    collection_file_id
   --------------------
   55555
   (1 row)

And, re-publish the messages, using the Django `shell <https://docs.djangoproject.com/en/4.2/ref/django-admin/#shell>`__ command, for example:

.. code-block:: python

   from process.util import get_publisher

   with get_publisher() as client:
      message = {"collection_id": 100, "collection_file_id": 55555}
      client.publish(message, routing_key="api_loader")

Freeze or unpublish a publication
---------------------------------

A publication is frozen if the source is temporarily broken or otherwise unavailable. Unfreeze the publication when the source is fixed.

A publication is unpublished if there are security concerns (like Afghanistan), if it duplicates another publication, or if it was added in error.

Only *delete* a publication if it is a duplicate or if it was otherwise created in error.

.. note::

   If the publication is no longer updated, or the spider is `removed from Kingfisher Collect <https://kingfisher-collect.readthedocs.io/en/latest/history.html>`__, set the retrieval frequency to ``NEVER``, instead of freezing the publication.

.. tip::

   To audit whether publications ought to be frozen, run `scrapy checkall <https://kingfisher-collect.readthedocs.io/en/latest/cli.html#checkall>`__ from Kingfisher Collect.

#. `Find the publication <https://data.open-contracting.org/admin/data_registry/collection/>`__
#. If freezing: Check *Frozen*, to stop jobs from being scheduled
#. If unpublishing: Uncheck *Public*, to hide the publication
#. Click *Save* at the bottom of the page

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
     Can view publications, licenses, jobs and job tasks
   Contributor
     Can add/change publications and licenses

#. Click *SAVE*

