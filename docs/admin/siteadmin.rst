Site administrators
===================

Use the `Django admin <https://data.open-contracting.org/admin/>`__ to:

-  Add a publication
-  Check the status of a job and its tasks

Once a new publication is added, the :ref:`cli-manageprocess` command runs at a regular interval, and advances each job by at most one task.

.. _admin-unpublish-freeze:

Unpublish or freeze a publication
---------------------------------

#. `Find the publication <https://data.open-contracting.org/admin/data_registry/collection/>`__
#. Uncheck *Public*, to hide the publication
#. Check *Frozen*, to stop jobs from being scheduled
#. Click *Save* at the bottom of the page

Only *delete* a publication if it is a duplicate or if it was otherwise created in error.

Add a user
----------

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

