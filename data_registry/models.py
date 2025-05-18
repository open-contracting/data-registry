from datetime import date, timedelta

from django.db import models
from django.db.models.functions import Now
from django.utils.translation import gettext_lazy as _


def format_datetime(dt):
    if isinstance(dt, Now):
        return "now"
    return dt.strftime("%d-%b-%y") if dt else ""


class JobQuerySet(models.QuerySet):
    def successful(self):
        """Return a query set of successfully completed jobs."""
        return self.complete().exclude(models.Exists(Task.objects.failed()))

    def unsuccessful(self):
        """Return a query set of unsuccessfully completed jobs."""
        return self.complete().filter(models.Exists(Task.objects.failed()))

    def complete(self):
        """Return a query set of complete jobs."""
        return self.filter(status=Job.Status.COMPLETED)

    def incomplete(self):
        """Return a query set of incomplete jobs."""
        return self.exclude(status=Job.Status.COMPLETED)


class Job(models.Model):
    class Status(models.TextChoices):
        #: Not in use.
        WAITING = "WAITING", "WAITING"
        #: The job is planned.
        PLANNED = "PLANNED", "PLANNED"
        #: The job has started.
        RUNNING = "RUNNING", "RUNNING"
        #: The job has ended (either successfully or unsuccessfully).
        COMPLETED = "COMPLETED", "COMPLETED"

    collection = models.ForeignKey("Collection", on_delete=models.CASCADE, db_index=True, verbose_name="publication")

    # Job metadata
    start = models.DateTimeField(blank=True, null=True, verbose_name="job started at")
    end = models.DateTimeField(blank=True, null=True, verbose_name="job ended at")
    status = models.TextField(choices=Status.choices, blank=True, default=Status.PLANNED)
    context = models.JSONField(
        blank=True,
        default=dict,
        help_text="<dl>"
        "<dt><code>spider</code></dt>"
        "<dd>The name of the spider in Kingfisher Collect</dd>"
        "<dt><code>data_version</code></dt>"
        "<dd>The data version of the crawl in Kingfisher Collect</dd>"
        "<dt><code>job_id</code></dt>"
        "<dd>The ID of the job in Scrapyd</dd>"
        "<dt><code>scrapy_log</code></dt>"
        "<dd>A local URL to the log file of the crawl in Scrapyd</dd>"
        "<dt><code>item_dropped_count</code></dt>"
        "<dd>The number of items dropped by the crawl</dd>"
        "<dt><code>invalid_json_count</code></dt>"
        "<dd>The number of invalid JSON items dropped by the crawl</dd>"
        "<dt><code>process_id</code></dt>"
        "<dd>The ID of the base collection in Kingfisher Process</dd>"
        "<dt><code>process_id_pelican</code></dt>"
        "<dd>The ID of the compiled collection in Kingfisher Process</dd>"
        "<dt><code>pelican_id</code></dt>"
        "<dd>The ID of the dataset in Pelican</dd>"
        "<dt><code>pelican_dataset_name</code></dt>"
        "<dd>The name of the dataset in Pelican</dd>"
        "</dl>",
    )
    process_notes = models.JSONField(
        blank=True,
        default=dict,
        help_text="The collection notes from Kingfisher Process.",
    )

    # Job logic
    archived = models.BooleanField(
        default=False,
        verbose_name="temporary data deleted",
        help_text="Whether the temporary data created by job tasks has been deleted.",
    )
    keep_all_data = models.BooleanField(
        default=False,
        verbose_name="preserve temporary data",
        help_text="By default, temporary data created by job tasks is deleted after the job "
        "is completed. Only the data registry's models' data and JSON exports are "
        "retained. To preserve temporary data for debugging, check this box. Then, "
        'when ready, uncheck this box and run the "manageprocess" management command.',
    )

    # Field coverage
    tenders_count = models.IntegerField(default=0)
    tenderers_count = models.IntegerField(default=0)
    tenders_items_count = models.IntegerField(default=0)
    parties_count = models.IntegerField(default=0)
    awards_count = models.IntegerField(default=0)
    awards_items_count = models.IntegerField(default=0)
    awards_suppliers_count = models.IntegerField(default=0)
    contracts_count = models.IntegerField(default=0)
    contracts_items_count = models.IntegerField(default=0)
    contracts_transactions_count = models.IntegerField(default=0)
    documents_count = models.IntegerField(default=0)
    plannings_count = models.IntegerField(default=0)
    milestones_count = models.IntegerField(default=0)
    amendments_count = models.IntegerField(default=0)

    # Collection metadata
    date_from = models.DateField(blank=True, null=True, verbose_name="minimum release date")
    date_to = models.DateField(blank=True, null=True, verbose_name="maximum release date")
    ocid_prefix = models.TextField(blank=True, verbose_name="OCID prefix")
    license = models.TextField(blank=True)
    publication_policy = models.TextField(blank=True)

    # Timestamps
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    objects = JobQuerySet.as_manager()

    def __str__(self):
        return f"{format_datetime(self.start)} .. {format_datetime(self.end)} ({self.pk})"

    def __repr__(self):
        return f"{self.collection!r}: {self}"

    def initiate(self):
        """Mark the job as started."""
        self.start = Now()
        self.status = Job.Status.RUNNING
        self.save()

    def complete(self):
        """Mark the job as ended."""
        self.end = Now()
        self.status = Job.Status.COMPLETED
        self.save()


class CollectionQuerySet(models.QuerySet):
    def visible(self):
        """Return a query set of public collections, exclude thosing without an active job for no reason."""
        return self.filter(public=True).exclude(active_job__isnull=True, no_data_rationale="")


class Collection(models.Model):
    class Region(models.TextChoices):
        #: Africa and Middle East
        MEA = "MEA", _("Africa and Middle East")
        #: Asia
        AS = "AS", _("Asia")
        #: Eastern Europe & Central Asia
        EECA = "EECA", _("Eastern Europe & Central Asia")
        #: Europe
        EU = "EU", _("Europe")
        #: Latin America & Caribbean
        LAC = "LAC", _("Latin America & Caribbean")
        #: North America
        NA = "NA", _("North America")
        #: Oceania
        OC = "OC", _("Oceania")

    class RetrievalFrequency(models.TextChoices):
        #: Monthly
        MONTHLY = "MONTHLY", _("Monthly")
        #: Every 6 months
        HALF_YEARLY = "HALF_YEARLY", _("Every 6 months")
        #: Annually
        ANNUALLY = "ANNUALLY", _("Annually")
        #: This dataset is no longer updated by the publisher
        NEVER = "NEVER", _("This dataset is no longer updated by the publisher")

    class UpdateFrequency(models.TextChoices):
        #: Unknown
        UNKNOWN = "UNKNOWN", _("Unknown")
        #: Real time
        REAL_TIME = "REAL_TIME", _("Real time")
        #: Hourly
        HOURLY = "HOURLY", _("Hourly")
        #: Daily
        DAILY = "DAILY", _("Daily")
        #: Weekly
        WEEKLY = "WEEKLY", _("Weekly")
        #: Monthly
        MONTHLY = "MONTHLY", _("Monthly")
        #: Every 3 months
        QUARTERLY = "QUARTERLY", _("Every 3 months")
        #: Every 6 months
        HALF_YEARLY = "HALF_YEARLY", _("Every 6 months")
        #: Annually
        ANNUALLY = "ANNUALLY", _("Annually")

    # Identification
    title = models.TextField(
        help_text='The name of the publication, following the <a href="https://docs.google.com/document/d/'
        '14ZXlAB6GWeK4xwDUt9HGi0fTew4BahjZQ2owdLLVp6I/edit#heading=h.t81hzvffylry">naming conventions</a>, '
        "and omitting the country name."
    )

    # Description
    description = models.TextField(
        blank=True,
        help_text="The first paragraph of the description of the publication, as Markdown text, following the "
        '<a href="https://docs.google.com/document/d/1Pr87zDrs9YY7BEvr_e6QjOy0gexs06dU9ES2_-V7Lzw/edit#heading='
        'h.fksp8fxgoi7v">template and guidance</a>.',
    )
    description_long = models.TextField(
        blank=True,
        help_text="The remaining paragraphs of the description of the publication, as Markdown text, "
        'which will appear under "Show more".',
    )

    # Spatial coverage
    country = models.TextField(
        blank=True, help_text="The official name of the country from which the data originates."
    )
    country_flag = models.TextField(blank=True)
    region = models.TextField(
        choices=Region.choices, blank=True, help_text="The name of the region to which the country belongs."
    )

    # Field coverage
    additional_data = models.TextField(
        blank=True,
        verbose_name="data availability",
        help_text="Any notable highlights about the available data, such as extensions used or additional fields,"
        " as Markdown text.",
    )

    # Language
    language = models.TextField(blank=True, help_text='The languages used within data fields: for example, "Spanish".')

    # Accrual periodicity
    update_frequency = models.TextField(
        choices=UpdateFrequency.choices,
        blank=True,
        default=UpdateFrequency.UNKNOWN,
        help_text="The frequency at which the source updates the publication.",
    )

    # Data quality
    summary = models.TextField(
        blank=True,
        verbose_name="quality summary",
        help_text="A short summary of quality issues, as Markdown text.",
    )
    last_reviewed = models.DateField(
        blank=True,
        null=True,
        verbose_name="last reviewed",
        help_text="The date on which the quality summary was last confirmed to be correct. "
        "Only the year and month are published.",
    )

    # License
    license_custom = models.ForeignKey(
        "License",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="data license",
        help_text="If not set, the Overview section will display the license URL within the OCDS package.",
    )

    # Documentation
    publication_policy = models.TextField(blank=True, verbose_name="publication policy")

    # Provenance
    source_url = models.TextField(blank=True, verbose_name="source URL", help_text="The URL of the publication.")

    # Job logic
    source_id = models.TextField(
        verbose_name="source ID",
        help_text="The name of the spider in Kingfisher Collect. If a new spider is not listed, "
        "Kingfisher Collect needs to be re-deployed to the registry's server.",
    )
    retrieval_frequency = models.TextField(
        choices=RetrievalFrequency.choices,
        blank=True,
        help_text="The frequency at which the registry updates the publication, based on the frequency at which "
        "the publication is updated.",
    )
    active_job = models.ForeignKey(
        "Job",
        on_delete=models.RESTRICT,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="active job",
        related_name="active_collection",
        help_text="A job is a set of tasks to collect and process data from a publication. "
        "A job can be selected once it is completed. If a new job completes, it becomes the active job.",
    )
    last_retrieved = models.DateField(
        blank=True, null=True, help_text="The date on which the most recent 'collect' job task completed."
    )
    frozen = models.BooleanField(
        default=False, help_text="If the spider is broken, check this box to prevent the scheduling of new jobs."
    )

    # Visibility logic
    no_data_rationale = models.TextField(
        blank=True,
        verbose_name="no data rationale",
        help_text="The short reason why the publication has no active job. If set, freeze the publication.",
    )
    public = models.BooleanField(
        default=False,
        help_text="If the active job's tasks completed without errors or 'No data rationale' is set, and all fields "
        "below in all languages are filled in, check this box to make the publication visible to anonymous users. "
        "Otherwise, it is visible to administrators only.",
    )

    # Timestamps
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    objects = CollectionQuerySet.as_manager()

    class Meta:
        verbose_name = "publication"

    def __str__(self):
        return f"{self.title} ({self.pk})"

    def __repr__(self):
        return f"{self.country}: {self}"

    def is_out_of_date(self):
        """
        Return whether the publication is out-of-date.

        A publication is out-of-date if it isn't frozen and has a retrieval frequency other than "never", and either
        has never been scheduled or was last scheduled longer ago than the retrieval frequency.
        """
        if self.frozen:
            return False

        # It has no retrieval frequency or the retrieval frequency is "never".
        if not self.retrieval_frequency or self.retrieval_frequency == self.RetrievalFrequency.NEVER:
            return False

        most_recent_job = self.job_set.order_by("-start").first()

        # It has never been scheduled.
        if not most_recent_job:
            return True

        # It has been scheduled, but not yet initiated.
        if not most_recent_job.start:
            return False

        match self.retrieval_frequency:
            case self.RetrievalFrequency.MONTHLY:
                days = 30
            case self.RetrievalFrequency.HALF_YEARLY:
                days = 180
            case self.RetrievalFrequency.ANNUALLY:
                days = 365
            case _:
                raise NotImplementedError

        return date.today() >= (most_recent_job.start + timedelta(days=days)).date()


class License(models.Model):
    name = models.TextField(blank=True, help_text="The official name of the license.")
    description = models.TextField(
        blank=True, help_text="A brief description of the permissions, conditions and limitations, as Markdown text."
    )
    url = models.TextField(blank=True, verbose_name="URL", help_text="The canonical URL of the license.")

    # Timestamps
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "data license"

    def __str__(self):
        return f"{self.name} ({self.pk})"


class TaskQuerySet(models.QuerySet):
    def failed(self):
        # https://docs.djangoproject.com/en/4.2/ref/models/expressions/#some-examples
        return Task.objects.filter(
            job=models.OuterRef("pk"),
            status=Task.Status.COMPLETED,
            result=Task.Result.FAILED,
        )


class Task(models.Model):
    class Status(models.TextChoices):
        #: The task has started, but work has not yet started in the application.
        #: (This status is never saved to the database.)
        WAITING = "WAITING", "WAITING"
        #: The task is planned.
        PLANNED = "PLANNED", "PLANNED"
        #: The task has started.
        RUNNING = "RUNNING", "RUNNING"
        #: The task has ended (either successfully or unsuccessfully).
        COMPLETED = "COMPLETED", "COMPLETED"

    class Result(models.TextChoices):
        #: The task ended successfully.
        OK = "OK", "OK"
        #: The task ended unsuccessfully.
        FAILED = "FAILED", "FAILED"

    class Type(models.TextChoices):
        #: Kingfisher Collect
        COLLECT = "collect"
        #: Kingfisher Process
        PROCESS = "process"
        #: Pelican
        PELICAN = "pelican"
        #: Exporter
        EXPORTER = "exporter"
        #: Flattener
        FLATTENER = "flattener"

    job = models.ForeignKey("Job", on_delete=models.CASCADE, db_index=True)

    # Task metadata
    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    status = models.TextField(choices=Status.choices, blank=True, default=Status.PLANNED)

    # Task result
    result = models.TextField(choices=Result.choices, blank=True)
    note = models.TextField(blank=True, help_text="Metadata about any failure.")

    # Job logic (see `create_tasks`)
    type = models.TextField(choices=Type.choices, blank=True)
    order = models.IntegerField(blank=True, null=True)

    # Timestamps
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    objects = TaskQuerySet.as_manager()

    class Meta:
        verbose_name = "job task"

    def __str__(self):
        return f"#{self.pk}({self.type})"

    def initiate(self):
        """Mark the task as started."""
        self.start = Now()
        self.status = Task.Status.RUNNING
        self.save()

    def progress(self, *, result="", note=""):
        """Update the task's progress. If called without arguments, reset the task's progress."""
        self.result = result
        self.note = note
        self.save()

    def complete(self, *, result, note=""):
        """Mark the task as ended."""
        self.end = Now()
        self.status = Task.Status.COMPLETED
        self.result = result
        self.note = note
        self.save()
