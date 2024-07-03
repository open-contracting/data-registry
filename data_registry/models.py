from datetime import date, timedelta

from django.db import models
from django.db.models.functions import Now
from django.utils.translation import gettext_lazy as _
from markdownx.models import MarkdownxField


def format_datetime(dt):
    if isinstance(dt, Now):
        return "now"
    return dt.strftime("%d-%b-%y") if dt else ""


class JobQuerySet(models.QuerySet):
    def active(self):
        """
        Return a query set of active jobs.
        """
        return self.filter(active=True)

    def complete(self):
        """
        Return a query set of complete jobs.
        """
        return self.filter(status=Job.Status.COMPLETED)

    def incomplete(self):
        """
        Return a query set of incomplete jobs.
        """
        return self.exclude(status=Job.Status.COMPLETED)


class Job(models.Model):
    collection = models.ForeignKey("Collection", on_delete=models.CASCADE, db_index=True, verbose_name="publication")
    start = models.DateTimeField(blank=True, null=True, verbose_name="job started at")
    end = models.DateTimeField(blank=True, null=True, verbose_name="job ended at")

    class Status(models.TextChoices):
        #: Not in use.
        WAITING = "WAITING", "WAITING"
        #: The job is planned.
        PLANNED = "PLANNED", "PLANNED"
        #: The job has started.
        RUNNING = "RUNNING", "RUNNING"
        #: The job has ended (either successfully or unsuccessfully).
        COMPLETED = "COMPLETED", "COMPLETED"

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

    active = models.BooleanField(
        default=False, help_text="Set this as the active job for the publication from the publication's page."
    )

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

    date_from = models.DateField(blank=True, null=True, verbose_name="minimum release date")
    date_to = models.DateField(blank=True, null=True, verbose_name="maximum release date")
    ocid_prefix = models.TextField(blank=True, verbose_name="OCID prefix")
    license = models.TextField(blank=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    objects = JobQuerySet.as_manager()

    def initiate(self):
        """
        Mark the job as started.
        """
        self.start = Now()
        self.status = Job.Status.RUNNING
        self.save()

    def complete(self):
        """
        Mark the job as ended.
        """
        self.end = Now()
        self.status = Job.Status.COMPLETED
        self.save()

    def __str__(self):
        return f"{format_datetime(self.start)} .. {format_datetime(self.end)} ({self.id})"

    def __repr__(self):
        return f"{repr(self.collection)}: {self}"


class CollectionQuerySet(models.QuerySet):
    def visible(self):
        """
        Return a query set of public collections with active jobs.
        """
        # https://docs.djangoproject.com/en/4.2/ref/models/expressions/#some-examples
        active_jobs = Job.objects.filter(collection=models.OuterRef("pk"), active=True)
        return self.filter(models.Exists(active_jobs), public=True)


class Collection(models.Model):
    class Meta:
        verbose_name = "publication"

    title = models.TextField(
        help_text='The name of the publication, following the <a href="https://docs.google.com/document/d/'
        '14ZXlAB6GWeK4xwDUt9HGi0fTew4BahjZQ2owdLLVp6I/edit#heading=h.t81hzvffylry">naming conventions</a>, '
        "and omitting the country name."
    )

    country = models.TextField(
        blank=True, help_text="The official name of the country from which the data originates."
    )
    country_flag = models.TextField(blank=True)

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

    region = models.TextField(
        choices=Region.choices,
        blank=True,
        help_text="The name of the region to which the country belongs.",
    )

    language = models.TextField(blank=True, help_text='The languages used within data fields: for example, "Spanish".')
    description = MarkdownxField(
        blank=True,
        help_text="The first paragraph of the description of the publication, as Markdown text, following the <a "
        'href="https://docs.google.com/document/d/1Pr87zDrs9YY7BEvr_e6QjOy0gexs06dU9ES2_-V7Lzw/edit#'
        'heading=h.fksp8fxgoi7v">template and guidance</a>.',
    )
    description_long = MarkdownxField(
        blank=True,
        help_text="The remaining paragraphs of the description of the publication, as "
        'Markdown text, which will appear under "Show more".',
    )
    last_retrieved = models.DateField(
        blank=True,
        null=True,
        help_text="The date on which the most recent 'collect' job task completed.",
    )

    license_custom = models.ForeignKey(
        "License",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="data license",
        help_text="If not set, the Overview section will display the license URL within the OCDS package.",
    )

    source_id = models.TextField(
        verbose_name="source ID",
        help_text="The name of the spider in Kingfisher Collect. If a new spider is not listed, "
        "Kingfisher Collect needs to be re-deployed to the registry's server.",
    )

    source_url = models.TextField(blank=True, verbose_name="source URL", help_text="The URL of the publication.")

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

    retrieval_frequency = models.TextField(
        choices=RetrievalFrequency.choices,
        blank=True,
        help_text="The frequency at which the registry updates the publication, based on the "
        "frequency at which the publication is updated.",
    )

    update_frequency = models.TextField(
        choices=UpdateFrequency.choices,
        blank=True,
        default=UpdateFrequency.UNKNOWN,
        help_text="The frequency at which the source updates the publication.",
    )

    summary = MarkdownxField(
        blank=True,
        verbose_name="quality summary",
        help_text="A short summary of quality issues, as Markdown text. Individual issues can be "
        "described below, which will be rendered as a bullet list.",
    )

    last_reviewed = models.DateField(
        blank=True,
        null=True,
        verbose_name="last reviewed",
        help_text="The date on which the quality summary was last confirmed to be correct. "
        "Only the year and month are published.",
    )

    additional_data = MarkdownxField(
        blank=True,
        verbose_name="data availability",
        help_text="Any notable highlights about the available data, such as extensions "
        "used or additional fields, as Markdown text.",
    )

    public = models.BooleanField(
        default=False,
        help_text="If the active job's tasks completed without errors and all the fields below in "
        "all languages are filled in, check this box to make the publication visible to "
        "anonymous users. Otherwise, it is visible to administrators only.",
    )
    frozen = models.BooleanField(
        default=False, help_text="If the spider is broken, check this box to prevent the scheduling of new jobs."
    )

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    objects = CollectionQuerySet.as_manager()

    def active_job(self):
        return self.job_set.active().first()

    def is_out_of_date(self):
        """
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

    def __str__(self):
        return f"{self.title} ({self.id})"

    def __repr__(self):
        return f"{self.country}: {self}"


class License(models.Model):
    class Meta:
        verbose_name = "data license"

    name = models.TextField(blank=True, help_text="The official name of the license.")
    description = MarkdownxField(
        blank=True,
        help_text="A brief description of the permissions, conditions and limitations, as Markdown text.",
    )
    url = models.TextField(blank=True, verbose_name="URL", help_text="The canonical URL of the license.")

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.id})"


class Issue(models.Model):
    class Meta:
        verbose_name = "quality issue"

    description = MarkdownxField(help_text="A one-line description of the quality issue, as Markdown text.")
    collection = models.ForeignKey("Collection", on_delete=models.CASCADE, db_index=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class Task(models.Model):
    class Meta:
        verbose_name = "job task"

    job = models.ForeignKey("Job", on_delete=models.CASCADE, db_index=True)
    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)

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

    status = models.TextField(choices=Status.choices, blank=True, default=Status.PLANNED)

    class Result(models.TextChoices):
        #: The task ended successfully.
        OK = "OK", "OK"
        #: The task ended unsuccessfully.
        FAILED = "FAILED", "FAILED"

    result = models.TextField(choices=Result.choices, blank=True)
    note = models.TextField(blank=True, help_text="Metadata about any failure.")
    context = models.JSONField(blank=True, default=dict)

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

    type = models.TextField(choices=Type.choices, blank=True)
    order = models.IntegerField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def initiate(self):
        """
        Mark the task as started.
        """
        self.start = Now()
        self.status = Task.Status.RUNNING
        self.save()

    def progress(self, *, result="", note=""):
        """
        Update the task's progress. If called without arguments, reset the task's progress.
        """
        self.result = result
        self.note = note
        self.save()

    def complete(self, *, result, note=""):
        """
        Mark the task as ended.
        """
        self.end = Now()
        self.status = Task.Status.COMPLETED
        self.result = result
        self.note = note
        self.save()

    def __str__(self):
        return f"#{self.id}({self.type})"
